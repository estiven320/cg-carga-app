# Resultados de referencia · Evidencia AA2-EV03

Valores calculados sobre `datos/ventas_tienda_tecnologia.csv` con el mismo
procedimiento que se le pide a Gemini. Sirven para **verificar** que lo que
responde la IA en el video es correcto.

> Puede haber diferencias pequeñas si Gemini elige otro criterio de imputación o
> de detección de atípicos. Eso no es un error: es una decisión metodológica, y en
> el video conviene mencionarla.

```
=== DIAGNOSTICO DEL DATASET CRUDO ===
Registros: 511 | Columnas: 11
Celdas vacias por columna: precio_unitario=21, total=28, calificacion_cliente=20
Total celdas vacias: 69
IDs duplicados: 31
Unidades negativas: 9
Variantes de "ciudad": 14 -> normalizadas: 7
Variantes de "categoria": 10 -> normalizadas: 5
Formatos de fecha detectados: YYYY-MM-DD, DD/MM/YYYY, DD-MM-YYYY
Totales escritos como moneda ($ 1.234.500): 106

=== LIMPIEZA PASO A PASO ===
R1 deduplicacion por id_venta: 31 eliminados -> 480
R2 normalizacion de texto: ciudad, categoria y metodo_pago homologados
R3 conversion de tipos: montos y fechas a formato unico
R4 validacion de dominio (unidades <= 0): 9 eliminados -> 471
R5 nulos criticos eliminados: 26 | valores imputados con la mediana: 37 -> 445
R6 atipicos IQR: Q1=649740 Q3=4360000 limite=9925390 | 56 eliminados -> 389
RETENCION FINAL: 389 de 511 = 76.1 %

=== SEGMENTACION POR CATEGORIA ===
Perifericos      ventas=111 ingreso= 272.099.750 ticket= 2.451.349 desc_prom=15.8%
Accesorios       ventas=103 ingreso=  86.207.310 ticket=   836.964 desc_prom=17.6%
Audio            ventas= 96 ingreso= 155.904.460 ticket= 1.624.005 desc_prom=17.6%
Almacenamiento   ventas= 49 ingreso=  46.701.370 ticket=   953.089 desc_prom=20.7%
Computadores     ventas= 30 ingreso= 220.941.400 ticket= 7.364.713 desc_prom=8.2%

=== REGRESION LINEAL: unidades ~ descuento_pct ===
n = 389
unidades = 2.0381 + 0.2210 * descuento_pct
R2 = 0.7957 | r de Pearson = 0.8920 | RMSE = 1.154 unidades
  descuento  0% -> 2.04 unidades estimadas
  descuento 10% -> 4.25 unidades estimadas
  descuento 20% -> 6.46 unidades estimadas
  descuento 30% -> 8.67 unidades estimadas
  descuento 40% -> 10.88 unidades estimadas

=== K-MEANS (k=3) sobre total, unidades y descuento_pct estandarizados ===
Convergencia en 15 iteraciones | inercia total = 403.74
Cluster 1: 179 ventas | ticket  1.153.484 | 3.7 unidades | 8.6 % de descuento
Cluster 2: 158 ventas | ticket  1.243.073 | 7.9 unidades | 25.6 % de descuento
Cluster 3:  52 ventas | ticket  7.287.983 | 6.0 unidades | 17.8 % de descuento
```
