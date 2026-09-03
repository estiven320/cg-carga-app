# CG CARGA · TMS open source

Sistema de gestión de transporte (TMS) para control logístico de entregas en tiempo real,
construido para operar con **costo de licencias de mapas e infraestructura = $0**.

```
apps/
  api/      NestJS + Prisma + PostgreSQL/PostGIS   (importación, geocodificación, POD, WhatsApp)
  web/      Next.js 15 + react-leaflet + Tailwind  (dashboard de despacho)
  mobile/   Flutter                                (app de conductores: rutas, GPS, evidencia)
infra/      docker-compose: PostGIS, MinIO, Evolution API, Nominatim self-host (opcional)
```

## Por qué cada pieza cuesta $0

| Necesidad | Solución elegida | Alternativa de pago que reemplaza |
|---|---|---|
| Mapa interactivo | `react-leaflet` + tiles de OpenStreetMap | Google Maps JS API |
| Geocodificación | Nominatim (OSM) + **caché en PostgreSQL** | Google Geocoding API |
| Datos geoespaciales | PostgreSQL + PostGIS | servicios geo administrados |
| Fotos de entrega (POD) | MinIO (S3 self-hosted) | S3 / Cloud Storage + egreso |
| Mensajería a conductores | Evolution API o Baileys (WhatsApp Web) | WhatsApp Cloud API por conversación |

El punto crítico es la **caché de geocodificación**: Nominatim público permite 1 petición/segundo.
Sin caché, reimportar la programación de un día sería inviable; con ella, la segunda corrida
resuelve el 100 % de las direcciones sin salir a la red.

---

## Puesta en marcha

```bash
cp .env.example .env
ln -sf ../../.env apps/api/.env      # el CLI de Prisma lee el .env de su propio directorio
npm install

npm run infra:up                     # PostGIS + MinIO + Evolution API
npm run db:migrate --workspace=apps/api
npm run db:seed --workspace=apps/api # datos de demostración

npm run dev:api                      # http://localhost:3001/api  (docs en /api/docs)
npm run dev:web                      # http://localhost:3000
```

App móvil:

```bash
cd apps/mobile
flutter pub get
flutter run --dart-define=API_URL=http://10.0.2.2:3001/api   # 10.0.2.2 = host desde el emulador
```

---

## Paso 1 · Arquitectura de datos

`apps/api/prisma/schema.prisma` — modelos `Route`, `Order`, `Client`, `DeliveryProof`,
más `GeocodeCache`, `Driver`, `DriverPing`, `ImportBatch`, `OrderEvent` y `Notification`.

Decisiones que vale la pena conocer:

- **PostGIS vía `Unsupported("geography(Point, 4326)")`.** Prisma no tipa PostGIS, así que la
  aplicación escribe únicamente `lat`/`lng` (que sí tipa) y unos **triggers**
  (`prisma/migrations/20260903000100_postgis_indexes/migration.sql`) mantienen la columna
  geográfica sincronizada. Resultado: ningún servicio necesita SQL crudo para insertar, y aun
  así quedan disponibles `ST_DWithin`, `ST_Distance` y el operador `<->` con índices GIST.
- **`GeocodeCache` guarda también los resultados negativos**, con TTL escalonado
  (error ≈30 min, no encontrado 7 días, acierto 180 días). Así una dirección que se sabe que
  falla no vuelve a consumir el cupo de 1 req/s en cada reimportación.
- **Idempotencia de la importación.** `Route` es único por `(code, dispatchDate)` y `Order` por
  `(routeId, documentNumber)`. Volver a subir el Excel corregido actualiza los datos pero
  conserva estados, coordenadas manuales y evidencias ya cargadas.
- **`DeliveryProof` nunca guarda binarios**: solo la llave del objeto en MinIO, su SHA-256
  (idempotencia de los reintentos offline de la app) y la distancia en metros entre la foto y la
  dirección geocodificada, que es la señal más útil para auditar una entrega dudosa.

## Paso 2 · Procesamiento del Excel y geocodificación

Flujo: `POST /api/import/dispatch` → `DispatchImportService`.

**Mapeo de columnas** (`modules/import/column-mapping.ts`). Los encabezados exactos del archivo
son `Número de documento`, `Nombre de cliente/proveedor`, `Direccion`, `Localidad / Municipio`,
`N/RUTA`, `Peso Kg`, `Unidades`, `Items` y `COMENTARIOS + TENER EN CUENTA`; el mapeo se hace
sobre encabezados normalizados con alias, porque en la práctica llegan con tildes, saltos de
línea y variaciones de redacción. La fila de encabezados se localiza escaneando las primeras 25
filas (los archivos traen título y filas en blanco arriba).

**Ventanas horarias** (`time-window.parser.ts`). `COMENTARIOS + TENER EN CUENTA` es texto libre;
el parser extrae rangos (`"DE 8:00 A 12:00"`, `"7 AM A 3 PM"`), límites (`"ANTES DE LAS 11"`,
`"DESPUES DE LA 1 PM"`) y citas (`"CITA 10:30"`). Lo que no reconoce queda en `null` y el
comentario crudo sigue visible en el dashboard y en la app: no se pierde información.

**Colores por `N/RUTA`** (`route-color.ts`). Asignación determinista sobre una paleta de 16
colores de alto contraste: la misma ruta siempre obtiene el mismo color, en el backend y en el
frontend, entre recargas y entre días.

**Rate limiting de Nominatim** (`modules/geocoding/`):

- `NominatimQueue` serializa **todas** las peticiones con un intervalo mínimo garantizado
  (1100 ms por defecto) y expone métricas y ETA.
- `NominatimClient` añade el `User-Agent` identificable que exige la política de la OSMF y
  reintenta con backoff exponencial ante 429/5xx.
- `GeocodingService` consulta primero la caché, deduplica peticiones en vuelo (30 filas con la
  misma dirección → 1 sola petición) y normaliza la dirección expandiendo la nomenclatura vial
  colombiana (`CRA`→`CARRERA`, `CLL`→`CALLE`…) y **agregando "Colombia"** a la búsqueda.

La importación es deliberadamente en dos fases: primero persiste (segundos, el despachador ve
las rutas de inmediato) y luego geocodifica en segundo plano a 1/s, emitiendo progreso por
WebSocket. Para 200 filas eso son ~3,5 minutos que no tienen por qué bloquear una petición HTTP.

## Paso 3 · Dashboard Next.js + mapa Leaflet

`apps/web/src/app/page.tsx` compone tres zonas: rutas a la izquierda, mapa al centro, KPIs y
acciones arriba.

- `components/map/DeliveryMap.tsx` — `react-leaflet` sobre tiles de OSM. Los marcadores son
  `divIcon` (no imágenes) porque el color viene de `N/RUTA` y es dinámico; se memoizan por
  combinación color+etiqueta+estado. Cada ruta dibuja además su polilínea, y **arrastrar un pin
  corrige la coordenada** de una dirección mal geocodificada sin salir del mapa.
- `components/map/MapPanel.tsx` — carga el mapa con `dynamic(..., { ssr: false })`, porque
  Leaflet toca `window` al importarse.
- El encuadre automático solo se dispara cuando cambia el conjunto de rutas visibles, no en cada
  refresco de datos: reencuadrar cada 60 segundos marearía al despachador.

### Sobre el diseño de Stitch

**El enlace de Stitch no pudo leerse desde este entorno.** El dominio `stitch.withgoogle.com`
está bloqueado por el proxy de red de la sesión y, además, los proyectos de Stitch requieren
sesión de Google, así que no son accesibles públicamente.

Para no bloquear la entrega, la UI se construyó con un **sistema de tokens completo** en
`apps/web/src/styles/tokens.css` y una paleta oscura de sala de control (estándar en TMS: el
mapa domina la pantalla y el cromo de la interfaz retrocede). Todos los componentes consumen
esas variables a través de Tailwind.

Para aplicar el diseño real: exporta la paleta desde Stitch y **reemplaza únicamente los valores
de `tokens.css`**. No hay que tocar ningún componente.

---

## Integraciones

**MinIO / POD.** La app Flutter pide una URL prefirmada (`POST /orders/:id/proofs/presign`),
sube la foto **directo al bucket** y confirma (`/confirm`). El API verifica contra MinIO que el
objeto exista antes de registrarlo, así no quedan evidencias fantasma. Existe además una ruta de
respaldo por proxy (`/upload`) para redes donde MinIO no es alcanzable desde el móvil.

**WhatsApp.** El proveedor se elige por variable de entorno (`WHATSAPP_PROVIDER`): Evolution API
(por defecto, corre en su propio contenedor y sobrevive a los redeploys del API) o Baileys
embebido (una sola máquina, sin contenedor extra). Los mensajes se persisten **antes** de
enviarse, de modo que si el gateway está caído quedan en cola y `POST /notifications/retry` los
recupera.

**Tiempo real.** Gateway de Socket.IO en `/realtime`: progreso de importación, cambios de estado
de las entregas y pings GPS de los conductores.

## Verificación

```bash
npm run build                              # API (nest build) + web (next build)
npx jest --workspace=apps/api              # 20 pruebas de los parsers
```

Los parsers críticos —mapeo de columnas, ventanas horarias, normalización de direcciones y
asignación de colores— tienen pruebas unitarias porque son la superficie donde el archivo real
de operaciones rompe supuestos.

## Límites conocidos

- `NominatimQueue` es un singleton **de proceso**. Con varias réplicas del API haría falta un
  rate limiter distribuido (token bucket en Redis) o, mejor, el Nominatim self-hosted del perfil
  `geocoder` de `docker-compose`, que elimina el límite por completo.
- `optimizeSequence` usa vecino más cercano con PostGIS. Es una mejora barata sobre el orden del
  Excel, no un VRP óptimo.
- La autenticación del conductor (cédula + celular) es adecuada para una flota conocida, no para
  un padrón abierto.
- `driver_pings` crece rápido; conviene particionarla por fecha o purgarla con un cron.
