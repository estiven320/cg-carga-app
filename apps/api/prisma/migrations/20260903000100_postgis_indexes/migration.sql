-- =============================================================================
-- PostGIS: indices espaciales + sincronizacion automatica lat/lng -> geom
--
-- Se ejecuta DESPUES de la migracion inicial generada por Prisma.
-- La aplicacion solo escribe `lat` y `lng` (tipos que Prisma si tipa); los
-- triggers de aqui mantienen la columna `geography(Point,4326)` al dia, de modo
-- que ningun servicio necesita SQL crudo para INSERT/UPDATE y aun asi quedan
-- disponibles ST_DWithin / ST_Distance / <-> para las consultas del mapa.
--
-- Se usa una funcion explicita por forma de tabla (lat/lng y last_lat/last_lng)
-- en lugar de una generica con EXECUTE dinamico: es mas simple de auditar y
-- evita el costo de planificar SQL en cada fila, algo que importa en
-- `driver_pings`, la tabla de mayor volumen del sistema.
-- =============================================================================

CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- --------------------------------------------------------------------------
-- Tablas con columnas `lat` / `lng` -> `geom`
-- --------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION tms_sync_geom()
RETURNS trigger AS $$
BEGIN
  IF NEW.lat IS NULL OR NEW.lng IS NULL THEN
    NEW.geom := NULL;
    RETURN NEW;
  END IF;

  IF NEW.lat < -90 OR NEW.lat > 90 OR NEW.lng < -180 OR NEW.lng > 180 THEN
    RAISE EXCEPTION 'Coordenada fuera de rango: lat=%, lng=%', NEW.lat, NEW.lng;
  END IF;

  NEW.geom := ST_SetSRID(ST_MakePoint(NEW.lng, NEW.lat), 4326)::geography;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- --------------------------------------------------------------------------
-- `drivers` guarda la ultima posicion en `last_lat` / `last_lng` -> `last_geom`
-- --------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION tms_sync_last_geom()
RETURNS trigger AS $$
BEGIN
  IF NEW.last_lat IS NULL OR NEW.last_lng IS NULL THEN
    NEW.last_geom := NULL;
    RETURN NEW;
  END IF;

  IF NEW.last_lat < -90 OR NEW.last_lat > 90 OR NEW.last_lng < -180 OR NEW.last_lng > 180 THEN
    RAISE EXCEPTION 'Coordenada fuera de rango: lat=%, lng=%', NEW.last_lat, NEW.last_lng;
  END IF;

  NEW.last_geom := ST_SetSRID(ST_MakePoint(NEW.last_lng, NEW.last_lat), 4326)::geography;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS orders_sync_geom ON "orders";
CREATE TRIGGER orders_sync_geom
  BEFORE INSERT OR UPDATE OF lat, lng ON "orders"
  FOR EACH ROW EXECUTE FUNCTION tms_sync_geom();

DROP TRIGGER IF EXISTS geocode_cache_sync_geom ON "geocode_cache";
CREATE TRIGGER geocode_cache_sync_geom
  BEFORE INSERT OR UPDATE OF lat, lng ON "geocode_cache"
  FOR EACH ROW EXECUTE FUNCTION tms_sync_geom();

DROP TRIGGER IF EXISTS delivery_proofs_sync_geom ON "delivery_proofs";
CREATE TRIGGER delivery_proofs_sync_geom
  BEFORE INSERT OR UPDATE OF lat, lng ON "delivery_proofs"
  FOR EACH ROW EXECUTE FUNCTION tms_sync_geom();

DROP TRIGGER IF EXISTS driver_pings_sync_geom ON "driver_pings";
CREATE TRIGGER driver_pings_sync_geom
  BEFORE INSERT OR UPDATE OF lat, lng ON "driver_pings"
  FOR EACH ROW EXECUTE FUNCTION tms_sync_geom();

DROP TRIGGER IF EXISTS drivers_sync_geom ON "drivers";
CREATE TRIGGER drivers_sync_geom
  BEFORE INSERT OR UPDATE OF last_lat, last_lng ON "drivers"
  FOR EACH ROW EXECUTE FUNCTION tms_sync_last_geom();

-- --------------------------------------------------------------------------
-- Indices espaciales (GIST) para consultas por viewport / cercania
-- --------------------------------------------------------------------------
CREATE INDEX IF NOT EXISTS orders_geom_gix          ON "orders"          USING GIST (geom);
CREATE INDEX IF NOT EXISTS geocode_cache_geom_gix   ON "geocode_cache"   USING GIST (geom);
CREATE INDEX IF NOT EXISTS delivery_proofs_geom_gix ON "delivery_proofs" USING GIST (geom);
CREATE INDEX IF NOT EXISTS driver_pings_geom_gix    ON "driver_pings"    USING GIST (geom);
CREATE INDEX IF NOT EXISTS drivers_last_geom_gix    ON "drivers"         USING GIST (last_geom);

-- --------------------------------------------------------------------------
-- Busqueda difusa de direcciones: permite sugerir un HIT de cache "parecido"
-- antes de gastar una peticion contra Nominatim.
-- --------------------------------------------------------------------------
CREATE INDEX IF NOT EXISTS geocode_cache_normalized_trgm
  ON "geocode_cache" USING GIN (normalized_query gin_trgm_ops);

CREATE INDEX IF NOT EXISTS orders_address_trgm
  ON "orders" USING GIN (address gin_trgm_ops);

-- --------------------------------------------------------------------------
-- Backfill por si ya existian filas con lat/lng antes de crear los triggers.
-- --------------------------------------------------------------------------
UPDATE "orders"          SET lat = lat WHERE lat IS NOT NULL AND geom IS NULL;
UPDATE "geocode_cache"   SET lat = lat WHERE lat IS NOT NULL AND geom IS NULL;
UPDATE "delivery_proofs" SET lat = lat WHERE lat IS NOT NULL AND geom IS NULL;
UPDATE "drivers"         SET last_lat = last_lat WHERE last_lat IS NOT NULL AND last_geom IS NULL;
