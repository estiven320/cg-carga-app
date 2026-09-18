# CG CARGA · Evidencia AA2-EV03

Consola de analítica de datos para la operación de transporte de CG CARGA y video de
la evidencia **AA2-EV03 · Video configuración de analítica de datos**.

Programa de formación: *Aplicación de la inteligencia artificial en la integración de datos*
· Resultado de aprendizaje **220501115-02**.

## Qué contiene la entrega

| Archivo | Descripción |
|---|---|
| `entrega/AA2-EV03-configuracion-analitica.mp4` | Video de 6:35 · 1280×720 · H.264. Recorre las siete etapas de configuración. |
| `entrega/AA2-EV03-entrega.pdf` | Documento de entrega con los datos generales, la justificación, el paso a paso y el espacio para el enlace del video. |
| `entrega/guion-narracion.md` | Guion con códigos de tiempo para narrar el video con voz propia. |
| `entrega/capturas/` | Fotogramas del video usados como figuras del documento. |

## La herramienta

`analitica/` es una consola que corre en el navegador, sin dependencias externas ni servicios en la nube.
El flujo tiene siete etapas:

1. **Justificación** — problema de negocio y alternativas evaluadas (Excel, Power BI, Looker Studio).
2. **Configuración inicial** — origen, delimitador, codificación, campo temporal, formato de fecha, moneda y granularidad.
3. **Importación y perfilado** — carga del CSV y diagnóstico automático de nulos, duplicados y tipos.
4. **Limpieza** — siete reglas: deduplicación, normalización de texto, conversión de tipos,
   validación de dominio, tratamiento de nulos con imputación por mediana, atípicos por rango
   intercuartil y enriquecimiento con campos calculados.
5. **Filtros y segmentación** — parámetros de análisis y comparación por tipo de vehículo.
6. **Algoritmos** — regresión lineal por mínimos cuadrados y K-Means con estandarización z-score.
7. **Resultados** — indicadores del pipeline y conclusiones.

El dataset `analitica/data/viajes_cg_carga.csv` simula el export semanal de la app de conductores
e incluye a propósito duplicados, nulos, formatos mixtos y valores atípicos, para que la etapa de
limpieza tenga algo real que corregir.

## Reproducir

```bash
npm install                      # playwright
node scripts/generar_dataset.js  # regenera el CSV (opcional, es determinista)
node scripts/servidor.js         # sirve la consola en http://localhost:4173
```

Con el servidor arriba, en otra terminal:

```bash
node scripts/grabar_video.mjs    # graba el MP4 y regenera el guion
node scripts/generar_pdf.mjs     # renderiza el PDF de entrega
```

La grabación usa el Chromium de Playwright (`/opt/pw-browsers/chromium`) y convierte el `.webm`
a MP4 con `ffmpeg`. `scripts/overlay.js` dibuja los subtítulos, el indicador de paso y el cursor
simulado; solo se inyecta durante la grabación, no forma parte de la consola.

## Antes de entregar

1. Grabe su voz sobre el video siguiendo `entrega/guion-narracion.md`.
2. Suba el MP4 a YouTube (no listado) o Google Drive con permiso de lectura pública.
3. Complete en `entrega/informe.html` sus datos personales y el enlace del video,
   y vuelva a ejecutar `node scripts/generar_pdf.mjs`.
