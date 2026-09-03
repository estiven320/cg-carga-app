-- =============================================================================
-- PostGIS: indices espaciales + sincronizacion automatica lat/lng -> geom
--
-- Se ejecuta DESPUES de la migracion inicial generada por Prisma.
-- La aplicacion solo escribe `lat` y `lng` (tipos que Prisma si tipa); los
-- triggers de aqui mantienen la columna `geography(Point,4326)` al dia, de modo
-- que ningun servicio necesita SQL crudo para INSERT/UPDATE y aun asi quedan
-- disponibles ST_DWithin / ST_Distance / <-> para las consultas del mapa.
-- =============================================================================

CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- --------------------------------------------------------------------------
-- Trigger generico: toma NEW.lat / NEW.lng y escribe NEW.<col geografica>
-- --------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION tms_sync_geom()
RETURNS trigger AS $$
DECLARE
  geom_column text := TG_ARGV[0];
  lat_column  text := COALESCE(TG_ARGV[1], 'lat');
  lng_column  text := COALESCE(TG_ARGV[2], 'lng');
  lat_value   double precision;
  lng_value   double precision;
BEGIN
  EXECUTE format('SELECT ($1).%I, ($1).%I', lat_column, lng_column)
    INTO lat_value, lng_value
    USING NEW;

  IF lat_value IS NULL OR lng_value IS NULL THEN
    NEW := jsonb_populate_record(NEW, jsonb_build_object(geom_column, NULL));
    RETURN NEW;
  END IF;

  -- Descarta coordenadas fuera de rango antes de construir el punto.
  IF lat_value < -90 OR lat_value > 90 OR lng_value < -180 OR lng_value > 180 THEN
    RAISE EXCEPTION 'Coordenada fuera de rango: lat=%, lng=%', lat_value, lng_value;
  END IF;

  NEW := jsonb_populate_record(
    NEW,
    jsonb_build_object(
      geom_column,
      ST_SetSRID(ST_MakePoint(lng_value, lat_value), 4326)::text
    )
  );
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- orders.geom
DROP TRIGGER IF EXISTS orders_sync_geom ON "orders";
CREATE TRIGGER orders_sync_geom
  BEFORE INSERT OR UPDATE OF lat, lng ON "orders"
  FOR EACH ROW EXECUTE FUNCTION tms_sync_geom('geom');

-- geocode_cache.geom
DROP TRIGGER IF EXISTS geocode_cache_sync_geom ON "geocode_cache";
CREATE TRIGGER geocode_cache_sync_geom
  BEFORE INSERT OR UPDATE OF lat, lng ON "geocode_cache"
  FOR EACH ROW EXECUTE FUNCTION tms_sync_geom('geom');

-- delivery_proofs.geom
DROP TRIGGER IF EXISTS delivery_proofs_sync_geom ON "delivery_proofs";
CREATE TRIGGER delivery_proofs_sync_geom
  BEFORE INSERT OR UPDATE OF lat, lng ON "delivery_proofs"
  FOR EACH ROW EXECUTE FUNCTION tms_sync_geom('geom');

-- driver_pings.geom
DROP TRIGGER IF EXISTS driver_pings_sync_geom ON "driver_pings";
CREATE TRIGGER driver_pings_sync_geom
  BEFORE INSERT OR UPDATE OF lat, lng ON "driver_pings"
  FOR EACH ROW EXECUTE FUNCTION tms_sync_geom('geom');

-- drivers.last_geom (usa columnas last_lat / last_lng)
DROP TRIGGER IF EXISTS drivers_sync_geom ON "drivers";
CREATE TRIGGER drivers_sync_geom
  BEFORE INSERT OR UPDATE OF last_lat, last_lng ON "drivers"
  FOR EACH ROW EXECUTE FUNCTION tms_sync_geom('last_geom', 'last_lat', 'last_lng');

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
