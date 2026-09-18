# Guion del video · Evidencia AA2-EV03

**Duración objetivo:** 7 a 9 minutos.
**Herramienta grabada:** Gemini (gemini.google.com).
**Archivo a subir:** `datos/ventas_tienda_tecnologia.csv`

## Antes de grabar

1. Abre una conversación **nueva** en Gemini, sin historial visible.
2. Ten abierto `guion/prompts-gemini.md` en otra ventana para copiar los prompts.
3. Cierra pestañas, notificaciones y cualquier dato personal en pantalla.
4. Graba con el navegador maximizado y el zoom al 100 % o 110 %, para que el texto
   se lea en el video.
5. Prueba el micrófono con 10 segundos de grabación antes de empezar en serio.

**Para grabar:** en Windows `Win + G` (Xbox Game Bar) o OBS Studio; en Mac
`Cmd + Shift + 5`; también sirve Loom o la grabación de pantalla de Google Meet.

---

## Minuto a minuto

| Tiempo | Qué se ve en pantalla | Qué dices |
|:---:|---|---|
| 00:00 – 00:35 | Pantalla de inicio de Gemini, sin escribir nada todavía | Te presentas: nombre completo, número de ficha y programa de formación. Enuncias la evidencia: «AA2-EV03, video de configuración de analítica de datos». Dices qué vas a hacer: procesar un archivo de ventas con una IA generativa, aplicando limpieza, segmentación y dos algoritmos. |
| 00:35 – 01:20 | Adjuntas el CSV y envías el **Prompt 1** | Explicas de dónde sale el archivo (ventas de una tienda de tecnología), cuántos registros trae y qué significa cada columna. Señalas en pantalla `descuento_pct` y `unidades`, que serán las variables del modelo. |
| 01:20 – 02:10 | **Prompt 2**, la tabla comparativa de herramientas | Justificas la elección: Gemini no requiere instalación ni licencia, ejecuta Python real sobre el archivo, documenta cada paso en lenguaje natural y permite corregir el análisis conversando. Mencionas por qué descartas Excel (limpieza manual sin registro) y Power BI (licencia). |
| 02:10 – 03:10 | **Prompt 3**, el diagnóstico de calidad | Lees en voz alta los hallazgos: 69 celdas vacías, 31 duplicados, 9 registros con unidades negativas, 3 formatos de fecha distintos y 106 totales escritos como texto con signo pesos. Concluyes que el dataset **no** se puede analizar tal como está. |
| 03:10 – 04:30 | **Prompt 4**, la limpieza regla por regla | Vas nombrando cada regla mientras aparece su conteo: deduplicación, normalización de texto, conversión de tipos, validación de dominio, tratamiento de nulos con imputación por mediana y atípicos por rango intercuartil. Cierras con el dato clave: de 511 registros quedan **389 válidos, el 76,1 %**. |
| 04:30 – 05:30 | **Prompt 5**, segmentaciones y filtros | Comparas las categorías: Periféricos vende más veces, pero Computadores tiene el ticket más alto con solo 30 ventas. Luego aplicas el filtro de Computadores y explicas que el filtro cambia la muestra sobre la que se ajustará el modelo. |
| 05:30 – 06:40 | **Prompt 6**, la regresión lineal y su gráfico | Lees la ecuación `unidades = 2,04 + 0,221 × descuento_pct`. Explicas el R² de **0,7957**: el descuento explica cerca del 80 % de la variación en unidades vendidas. Interpretas la pendiente: cada punto de descuento vende ~0,22 unidades más, o sea ~2,2 unidades por cada 10 puntos. |
| 06:40 – 07:50 | **Prompt 7**, K-Means y su gráfico de clusters | Explicas que es un algoritmo **no supervisado**: nadie le dijo cómo agrupar. Describes los tres segmentos: ticket bajo con poco descuento, volumen con descuento alto, y ticket alto de computadores. Dices qué harías con cada uno. |
| 07:50 – 08:30 | **Prompt 8**, las conclusiones | Recapitulas las seis etapas configuradas: contexto, justificación, diagnóstico, limpieza, segmentación y algoritmos. Cierras agradeciendo al instructor. |

---

## Cómo cumple cada criterio del instrumento

| # | Criterio de la lista de verificación | Dónde se cumple |
|:-:|---|---|
| 1 | El video presenta el paso a paso de la configuración inicial | Minutos 00:35 – 02:10: subida del archivo, definición del rol, reglas de trabajo por etapas y contrato de salida (código + tablas) |
| 2 | Se justifica la elección de la herramienta | Minuto 01:20 – 02:10, con la tabla comparativa frente a Excel, Power BI y Python a mano |
| 3 | Se evidencia la importación y limpieza básica | Minutos 02:10 – 04:30: diagnóstico de calidad y las siete reglas con su conteo |
| 4 | Se aplican filtros, segmentaciones o parámetros | Minuto 04:30 – 05:30: segmentación por categoría y ciudad, más dos filtros |
| 5 | Se implementa al menos una técnica o algoritmo | Minutos 05:30 – 07:50: **dos** algoritmos, regresión lineal y K-Means |
| 6 | La narración es clara, técnica y bien estructurada | Este guion: una idea por bloque, cifras concretas y cierre recapitulativo |
| 7 | El PDF incluye los datos requeridos y el enlace al video | `entrega/AA2-EV03-entrega.pdf`, una vez completes tus datos y el enlace |

---

## Errores que cuestan puntos

- **Leer el guion palabra por palabra.** Habla de los números que ves en pantalla; si
  Gemini devuelve una cifra distinta a la de referencia, di la que salió y por qué
  puede variar (el modelo elige el criterio de imputación o de atípicos).
- **Pasar los prompts sin explicar.** El criterio 1 evalúa que se vea la
  *configuración*, no solo el resultado. Di qué le estás pidiendo y para qué.
- **Silencios largos mientras Gemini procesa.** Aprovecha esos segundos para explicar
  lo que acabas de pedir o lo que esperas recibir.
- **Zoom pequeño.** Si el evaluador no puede leer las tablas, los criterios 3, 4 y 5
  quedan sin evidencia.
- **Olvidar el enlace.** El criterio 7 exige un enlace **funcional**: ábrelo en una
  ventana de incógnito antes de entregar.
