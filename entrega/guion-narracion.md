# Guion de narración · Evidencia AA2-EV03

**Video:** Configuración de una herramienta de analítica de datos — CG CARGA
**Archivo:** `entrega/AA2-EV03-configuracion-analitica.mp4`

Los códigos de tiempo corresponden al video generado. Cada línea es el texto que
aparece como subtítulo en pantalla y que debe narrarse en voz propia.

| Tiempo | Narración |
|:------:|:----------|
| `00:00` | PORTADA · Presentarse: nombre completo, ficha y programa de formación. Enunciar la evidencia AA2-EV03. |
| `00:10` | La operación de CG CARGA genera cada semana un archivo de viajes exportado desde la app de conductores. |
| `00:16` | Ese archivo llega con registros repetidos, celdas vacías, montos con símbolo de moneda y fechas en tres formatos distintos. |
| `00:24` | Se evaluaron Excel, Power BI y Looker Studio. Se eligió una consola propia por reproducibilidad, trazabilidad, costo cero y portabilidad. |
| `00:34` | El flujo tiene siete etapas y aplica técnicas concretas: deduplicación, imputación, rango intercuartil, regresión lineal y K-Means. |
| `00:45` | Primer paso de la configuración: declarar el origen de datos y el contrato que debe cumplir el archivo. |
| `00:53` | Se define el archivo fuente, la coma como delimitador y UTF-8 como codificación, que es lo que exporta la aplicación móvil. |
| `01:03` | La granularidad de agregación se fija en mensual, porque así se revisa la operación en los comités de la empresa. |
| `01:12` | En el contrato de datos se marca "fecha" como campo temporal, formato día, mes y año, moneda en pesos colombianos y zona horaria de Bogotá. |
| `01:26` | Al guardar, el estado pasa a CONFIGURADO y la consola deja registrado cada parámetro. La conexión ya está lista para importar. |
| `01:37` | Con la configuración guardada se importa el conjunto de datos. |
| `01:43` | Se cargaron 554 registros y 12 campos. La consola ejecuta de inmediato un perfilado de calidad. |
| `01:49` | El perfilado detecta 70 celdas vacías, 34 identificadores duplicados y 15 viajes con distancia negativa. |
| `01:57` | En la vista previa las celdas rojas son valores vacíos y las ámbar tienen formato inconsistente: montos con signo pesos y ciudades en mayúsculas. |
| `02:08` | El perfilado por campo infiere el tipo de dato de cada columna y cuenta nulos y valores distintos. Estos datos no se pueden analizar todavía. |
| `02:20` | Cuarto paso: la limpieza. Se activan seis reglas de calidad y cada una queda registrada con los registros que afecta. |
| `02:27` | R1 deduplica por identificador de viaje. R2 normaliza el texto. R3 convierte tipos: los montos pasan a número y las fechas a formato ISO. |
| `02:37` | R4 valida el dominio y descarta distancias menores o iguales a cero. R5 elimina nulos críticos e imputa peso y duración con la mediana. |
| `02:46` | R6 aplica la técnica del rango intercuartil para retirar los fletes atípicos por encima de Q3 más 1,5 veces el IQR. |
| `02:57` | La consola reporta cada regla ejecutada con su conteo exacto: 34 duplicados, 52 registros inválidos o nulos y 27 atípicos. |
| `03:06` | Del total original quedan 441 registros válidos, una retención del 79,6 por ciento del volumen. |
| `03:13` | El dataset resultante ya está tipado y enriquecido con los campos calculados costo por kilómetro, rendimiento y ruta. |
| `03:24` | Quinto paso: parametrizar el análisis con filtros y segmentaciones. |
| `03:31` | Sin filtros se analiza el universo completo: 441 viajes, 829 millones de pesos en flete y un ticket promedio de 1,88 millones. |
| `03:40` | La segmentación por tipo de vehículo compara kilómetros, flete y costo unitario entre categorías. El turbo es el de mayor costo por kilómetro. |
| `03:51` | Ahora se aplica un filtro real: solo viajes entregados con tractomula y distancia mínima de 200 kilómetros. |
| `04:03` | El subconjunto se recalcula al instante y todos los indicadores responden al filtro aplicado. |
| `04:13` | Ese recorte deja solo 34 viajes: sirve para una revisión puntual, pero son pocas observaciones para ajustar un modelo. |
| `04:24` | Se libera la distancia mínima y se conserva la flota de tractomulas efectivamente entregadas: un segmento homogéneo, que es lo correcto para calcular un tarifario por kilómetro. |
| `04:37` | Sexto paso: aplicar los algoritmos sobre el subconjunto ya depurado y filtrado. |
| `04:42` | El primero es una regresión lineal por mínimos cuadrados que predice el flete a partir de la distancia recorrida. |
| `04:53` | La consola entrega la ecuación estimada, el coeficiente de determinación R cuadrado, la correlación de Pearson y los errores RMSE y MAE. |
| `05:03` | La nube de puntos con la recta de ajuste muestra la relación, y la tabla simula el flete estimado para rutas de 200, 450 y 800 kilómetros. |
| `05:12` | Esa pendiente es el tarifario base por kilómetro que la empresa puede usar para cotizar rutas nuevas. |
| `05:20` | El segundo algoritmo es K-Means, un agrupamiento no supervisado con tres clusters sobre distancia, peso y costo estandarizados. |
| `05:32` | K-Means converge en pocas iteraciones y separa la operación en tres perfiles logísticos sin usar etiquetas previas. |
| `05:41` | Cada cluster queda caracterizado con su número de viajes, kilómetros, peso, flete y costo unitario promedio. |
| `05:49` | El gráfico muestra los tres grupos diferenciados por color, lo que permite priorizar dónde renegociar tarifas. |
| `05:59` | Séptimo y último paso: los resultados del proceso completo de configuración. |
| `06:04` | Se procesaron 554 registros crudos, quedaron 441 registros válidos con 79,6 por ciento de calidad final, más el R cuadrado del modelo y los tres segmentos identificados. |
| `06:16` | Las conclusiones resumen el aporte de cada etapa y dejan el tablero parametrizado y reproducible para el próximo archivo de la app de conductores. |
| `06:27` | CIERRE · Recapitular las siete etapas y despedirse agradeciendo al instructor. |

**Duración aproximada:** 06:27 más el cierre.
