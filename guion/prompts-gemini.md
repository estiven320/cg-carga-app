# Prompts para Gemini · Evidencia AA2-EV03

Copia y pega cada bloque **en orden**, en una sola conversación de
[gemini.google.com](https://gemini.google.com). Sube primero el archivo
`datos/ventas_tienda_tecnologia.csv` con el botón de adjuntar (el clip o el `+`).

> Graba la pantalla desde antes de subir el archivo. Cada prompt corresponde a un
> criterio de la lista de verificación del instrumento de evaluación.

---

## Prompt 1 · Rol y contexto

> Actúa como analista de datos. Voy a configurar contigo un análisis completo de un
> archivo de ventas de una tienda de tecnología. Trabajaremos por etapas y en cada una
> quiero que muestres el código Python que ejecutas y los resultados en tablas.
> No avances a la etapa siguiente hasta que yo te lo pida.
>
> Primera etapa: acabo de subir el archivo `ventas_tienda_tecnologia.csv`. Descríbeme
> su estructura: cuántos registros y columnas tiene, el tipo de dato de cada columna y
> una muestra de las primeras 10 filas.

**Qué debe salir:** 511 registros, 11 columnas. Menciona `id_venta`, `fecha`, `ciudad`,
`categoria`, `producto`, `unidades`, `precio_unitario`, `descuento_pct`, `total`,
`metodo_pago`, `calificacion_cliente`.

**Qué narrar:** por qué eliges Gemini como herramienta de analítica (ver Prompt 2).

---

## Prompt 2 · Justificación de la herramienta

> Antes de seguir: justifica técnicamente por qué una IA generativa como tú es una
> herramienta válida de analítica de datos para este caso, comparándola con Excel,
> Power BI y un script de Python escrito a mano. Preséntalo en una tabla con las
> columnas: herramienta, ventaja principal, limitación frente a este caso.

**Qué narrar mientras responde:** tus propios criterios de elección — no requiere
instalación ni licencia, ejecuta Python real sobre el archivo, documenta cada paso
en lenguaje natural y permite iterar sin reescribir código.

---

## Prompt 3 · Diagnóstico de calidad de los datos

> Segunda etapa: haz un diagnóstico de calidad del dataset. Repórtame en una tabla:
>
> 1. Celdas vacías por columna.
> 2. Registros duplicados según `id_venta`.
> 3. Valores fuera de dominio (por ejemplo `unidades` menores o iguales a cero).
> 4. Cuántos formatos distintos de fecha aparecen en la columna `fecha` y cuáles son.
> 5. Cuántos valores de `total` y `precio_unitario` están escritos como texto con
>    símbolo de moneda en lugar de número.
> 6. Cuántas variantes de escritura tienen `ciudad` y `categoria` por mayúsculas o
>    espacios sobrantes.
>
> Al final dime en una frase si el dataset se puede analizar tal como está.

**Valores de referencia:** 69 celdas vacías (21 en `precio_unitario`, 28 en `total`,
20 en `calificacion_cliente`), 31 duplicados, 9 registros con unidades negativas,
3 formatos de fecha, 106 totales escritos como moneda, 14 variantes de ciudad para
7 ciudades reales y 10 variantes de categoría para 5 categorías reales.

---

## Prompt 4 · Limpieza y transformación

> Tercera etapa: limpia el dataset aplicando estas reglas en este orden y dime cuántos
> registros afecta cada una:
>
> - **R1** Elimina duplicados usando `id_venta` como clave.
> - **R2** Normaliza el texto de `ciudad`, `categoria` y `metodo_pago`: quita espacios
>   sobrantes y unifica mayúsculas en formato título.
> - **R3** Convierte a número `total`, `precio_unitario`, `unidades`, `descuento_pct` y
>   `calificacion_cliente`, quitando el símbolo `$` y los separadores de miles.
>   Unifica `fecha` al formato `YYYY-MM-DD` reconociendo los tres formatos de entrada.
> - **R4** Elimina los registros con `unidades` menores o iguales a cero.
> - **R5** Elimina los registros sin `total`, `unidades` o `descuento_pct`. Los nulos
>   de `precio_unitario` y `calificacion_cliente` impútalos con la mediana.
> - **R6** Detecta y elimina los atípicos de `total` con el método del rango
>   intercuartil: descarta lo que supere Q3 + 1,5 × IQR. Dime el valor de Q1, Q3 y
>   del límite superior.
> - **R7** Crea las columnas calculadas `mes` (a partir de la fecha) y
>   `precio_efectivo` = `total` / `unidades`.
>
> Muéstrame una tabla resumen con el conteo de registros antes y después de cada regla
> y el porcentaje de retención final.

**Valores de referencia:** 511 → 480 (R1, −31) → 471 (R4, −9) → 445 (R5, −26 eliminados
y 37 imputados) → **389 registros válidos** (R6, −56; límite IQR ≈ $ 9.925.390).
Retención final **76,1 %**.

---

## Prompt 5 · Filtros y segmentación

> Cuarta etapa: sobre el dataset limpio quiero parametrizar el análisis.
>
> 1. Segmenta por `categoria` y dame una tabla con: número de ventas, ingreso total,
>    ticket promedio y descuento promedio por categoría, ordenada por ingreso.
> 2. Segmenta por `ciudad` con los mismos indicadores.
> 3. Ahora aplica un filtro: solo las ventas de la categoría `Computadores`. Dime
>    cuántos registros quedan y cómo cambian los indicadores frente al total.
> 4. Quita ese filtro y en su lugar deja solo las ventas con `descuento_pct` mayor o
>    igual a 20. ¿Cuántas son y qué representan del ingreso total?

**Valores de referencia por categoría:** Periféricos 111 ventas / $ 272,1 M;
Computadores 30 ventas / $ 220,9 M y el ticket más alto ($ 7,36 M);
Audio 96 / $ 155,9 M; Accesorios 103 / $ 86,2 M; Almacenamiento 49 / $ 46,7 M.

**Qué narrar:** que los filtros no son decorativos — cambian la muestra sobre la que
se ajusta el modelo, y por eso se definen antes de aplicar el algoritmo.

---

## Prompt 6 · Algoritmo 1 — Regresión lineal

> Quinta etapa: aplica una técnica de análisis. Ajusta una **regresión lineal simple
> por mínimos cuadrados** sobre el dataset limpio completo, con `descuento_pct` como
> variable predictora y `unidades` como variable objetivo.
>
> Entrégame:
>
> 1. La ecuación estimada con sus coeficientes.
> 2. El coeficiente de determinación R², el coeficiente de correlación de Pearson y
>    el RMSE.
> 3. Un gráfico de dispersión con la recta de ajuste.
> 4. La predicción de unidades para descuentos de 0 %, 10 %, 20 %, 30 % y 40 %.
> 5. Una interpretación en lenguaje de negocio: ¿cuántas unidades adicionales se
>    venden por cada punto porcentual de descuento?

**Valores de referencia:** `unidades = 2,0381 + 0,2210 × descuento_pct`,
R² = **0,7957**, r de Pearson = **0,8920**, RMSE ≈ 1,15 unidades.
Interpretación: cada punto de descuento agrega ~0,22 unidades; 10 puntos, ~2,2 unidades.

---

## Prompt 7 · Algoritmo 2 — Agrupamiento K-Means

> Sexta etapa: aplica ahora una técnica no supervisada. Ejecuta **K-Means con k = 3**
> sobre las variables `total`, `unidades` y `descuento_pct`, estandarizadas con z-score.
>
> Entrégame:
>
> 1. El número de iteraciones hasta converger y la inercia total.
> 2. Una tabla con el perfil de cada cluster: número de ventas, ticket promedio,
>    unidades promedio y descuento promedio.
> 3. Un nombre descriptivo para cada cluster según su perfil comercial.
> 4. Un gráfico de dispersión con los clusters diferenciados por color.
> 5. Qué decisión comercial tomarías con cada segmento.

**Valores de referencia:** 3 clusters — ~179 ventas de ticket bajo con poco descuento
(~8,6 %), ~158 ventas de volumen con descuento alto (~25,6 %) y ~52 ventas de ticket
alto (~$ 7,3 M, dominadas por Computadores). Inercia ≈ 404.

---

## Prompt 8 · Conclusiones

> Última etapa: cierra el análisis. Dame cinco conclusiones accionables numeradas que
> se desprendan de todo lo que hicimos — el diagnóstico de calidad, la limpieza, la
> segmentación, la regresión y el K-Means. Cada conclusión debe citar un número
> concreto obtenido en el análisis.

**Qué narrar:** recapitula las seis etapas configuradas y cierra agradeciendo al
instructor.

---

## Prompt 9 · Opcional, si tu cuenta lo permite

> Exporta el código completo del análisis a Google Colab y el dataset limpio a Google
> Sheets.

Si el botón de exportar no aparece en tu cuenta, dilo en el video y sigue adelante:
no es un criterio de la lista de verificación.
