# Prompts para grabar desde el celular · Evidencia AA2-EV03

Versión corta de los prompts, pensada para pegar desde un teléfono y para que las
respuestas se lean en pantalla angosta. Son **ocho**, en este orden, en una sola
conversación de la app de ChatGPT o Gemini.

## Antes de empezar

1. **Ten el CSV en el teléfono.** Descarga `ventas_tienda_tecnologia.csv` desde el chat
   o desde el repositorio y guárdalo en Archivos o en Google Drive.
2. Abre la app de la IA, **conversación nueva**, e inicia sesión.
3. Activa la grabación de pantalla **con micrófono**:
   - **Android:** ajustes rápidos → Grabar pantalla → activar audio del micrófono.
   - **iPhone:** Ajustes → Centro de control → agregar Grabación de pantalla; luego
     mantén pulsado el botón para activar el micrófono.
4. Gira el teléfono a **horizontal** cuando la IA muestre tablas: se leen mucho mejor y
   los criterios 3, 4 y 5 se califican por lo que el instructor alcance a leer.

---

## 1 · Rol y estructura

```
Actúa como analista de datos. Vamos a analizar por etapas el archivo que adjunto.
Reglas: usa Python real sobre el archivo, muestra el código que ejecutas, y no avances
de etapa hasta que te lo pida. Leo en un teléfono: usa tablas de máximo 3 columnas y
respuestas cortas.
Etapa 1: dime cuántos registros y columnas tiene y qué significa cada columna.
```

**Debe decir:** 511 registros, 11 columnas.

## 2 · Justificación

```
Etapa 2: justifica en una tabla de 3 columnas por qué una IA generativa con ejecución
de código sirve como herramienta de analítica, frente a Excel, Power BI y un script de
Python hecho a mano. Columnas: herramienta, ventaja, limitación.
```

**Mientras responde, narra:** no requiere instalar ni licenciar nada, ejecuta Python
real sobre el archivo, y deja documentado cada paso en lenguaje natural.

## 3 · Diagnóstico de calidad

```
Etapa 3: diagnostica la calidad del dataset. En una tabla corta dime: celdas vacías por
columna, duplicados por id_venta, registros con unidades menores o iguales a cero,
cuántos formatos de fecha distintos hay, y cuántos valores de total están escritos como
texto con símbolo de moneda. Cierra diciendo si se puede analizar así.
```

**Debe decir:** 69 celdas vacías · 31 duplicados · 9 unidades negativas · 3 formatos de
fecha · 106 totales como texto. Y que **no** se puede analizar así.

## 4 · Limpieza

```
Etapa 4: limpia el dataset en este orden y dime cuántos registros elimina cada regla.
R1 duplicados por id_venta. R2 normaliza texto de ciudad y categoria. R3 convierte a
número total, precio_unitario, unidades y descuento_pct, y unifica fecha a YYYY-MM-DD.
R4 elimina unidades menores o iguales a cero. R5 elimina nulos de total, unidades y
descuento_pct, e imputa precio_unitario y calificacion_cliente con la mediana.
R6 elimina atípicos de total por encima de Q3 + 1,5 por IQR.
Dame una tabla con el conteo después de cada regla y la retención final en porcentaje.
```

**Debe decir:** 511 → 480 → 471 → 445 → **389 registros**, retención **76,1 %**.

## 5 · Segmentación y filtro

```
Etapa 5: segmenta el dataset limpio por categoria. Tabla con ventas, ingreso total y
ticket promedio por categoría, ordenada por ingreso. Después aplica un filtro de solo
categoria Computadores y dime cómo cambian los indicadores.
```

**Debe decir:** Periféricos 111 ventas / $ 272,1 M · Computadores 30 ventas / $ 220,9 M
con el ticket más alto ($ 7,36 M).

## 6 · Regresión lineal

```
Etapa 6: ajusta una regresión lineal simple por mínimos cuadrados con descuento_pct
como variable predictora y unidades como objetivo. Dame la ecuación, el R cuadrado, la
correlación de Pearson, un gráfico de dispersión con la recta, y la predicción de
unidades para descuentos de 0, 10, 20, 30 y 40 por ciento.
```

**Debe decir:** `unidades = 2,04 + 0,221 × descuento_pct` · **R² = 0,7957** ·
r = 0,8920. Narra: cada punto de descuento vende ~0,22 unidades más.

## 7 · K-Means

```
Etapa 7: ejecuta K-Means con k igual a 3 sobre total, unidades y descuento_pct
estandarizadas con z-score. Dame las iteraciones hasta converger, un gráfico de los
clusters por color, y una tabla con ventas, ticket promedio y descuento promedio de cada
cluster, más un nombre descriptivo para cada uno.
```

**Debe decir:** 3 clusters de ~179, ~158 y ~52 ventas. Narra que es **no supervisado**:
nadie le dio las etiquetas.

## 8 · Conclusiones

```
Etapa 8: dame cinco conclusiones accionables numeradas y cortas, cada una citando una
cifra concreta del análisis.
```

**Para cerrar, narra tú:** recapitula las etapas y agradece al instructor.

---

## Si algo se tuerce

| Qué pasa | Qué escribes |
|---|---|
| Responde sin mostrar el código | `Muéstrame el código Python que ejecutaste.` |
| Dice que no encuentra el archivo | Lo vuelves a adjuntar y lo dices con naturalidad en el video |
| Se salta una etapa | `Volvamos a la etapa 4, aún no terminamos.` |
| Hace tablas muy anchas | `Rehazlo con tablas de máximo 3 columnas, leo en un teléfono.` |
| Da un número distinto al de referencia | Di el que salió y menciona que el criterio de imputación o de atípicos es una decisión metodológica |
