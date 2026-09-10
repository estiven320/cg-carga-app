# Matriz de Novedades · Logística y Transporte

Un solo archivo Excel para registrar todo lo que sale mal en una entrega, saber a quién
cobrárselo y medir si la operación está mejorando.

| Archivo | Para qué |
|---|---|
| `MATRIZ_NOVEDADES_LOGISTICA_TRANSPORTE.xlsx` | El archivo de trabajo, vacío y listo para usar |
| `MATRIZ_NOVEDADES_LOGISTICA_TRANSPORTE_EJEMPLO.xlsx` | El mismo archivo con un mes de datos ficticios, para ver el tablero funcionando |
| `generar_matriz.py` | Genera el archivo de trabajo (`pip install openpyxl && python3 generar_matriz.py`) |
| `crear_ejemplo.py` | Genera la versión con datos de muestra |

Diseño genérico: sirve para cualquier operación de transporte. No depende de ningún archivo previo.

---

## Base conceptual

| Concepto | De dónde sale |
|---|---|
| **OTIF / DIFOT** como métrica reina | Estándar de la industria: un envío solo cuenta como bueno si llegó *a tiempo* **y** *completo* |
| **Carrier scorecard** con nota A/B/C/D | Práctica estándar de evaluación de transportadoras: OTIF, tasa de excepciones, días de resolución y valor en riesgo en una sola línea por empresa |
| **Causa raíz clasificada en 6M** | Diagrama de Ishikawa: Método, Material, Medición, Mano de obra, Máquina, Medio ambiente |
| **Tipos de novedad** | Códigos habituales de entrega fallida: cliente ausente, rechazo, dirección errada, avería, faltante, contraentrega fallida, etc. |
| **Pareto 80/20 de causas** | Para atacar primero las pocas causas que explican casi todo |

---

## Las cinco hojas

| Hoja | Para qué |
|---|---|
| `INICIO` | Cómo se usa, en tres pasos |
| `TABLERO` | KPIs, scorecard de transportadoras, Pareto, buscador de guía |
| `NOVEDADES` | La matriz: una fila por incidencia |
| `ENVIOS` | Base de despachos: una fila por envío |
| `CONFIG` | Catálogos y reglas de negocio |

**Llave de cruce:** el `Nº Guía / Remisión`. Se digita en `NOVEDADES!C` y trae todo desde `ENVIOS`.

### Convención de colores

| | Significado |
|---|---|
| 🟨 Amarillo `#FEF3C7` | Se digita |
| ⬜ Gris `#F8FAFC` | Se calcula solo |
| Encabezado dorado | Columna de captura |
| Encabezado azul | Columna calculada |

Cada hoja además tiene una banda oscura arriba que separa las zonas.

---

## Hoja `ENVIOS`

16 columnas. Se digitan 11, se calculan 5.

| Col | Encabezado | Tipo | Fórmula |
|---|---|---|---|
| **A** | **Nº Guía / Remisión** | 🟨 **LLAVE** | — |
| B | Fecha despacho | 🟨 | — |
| C | Cliente | 🟨 | — |
| D | Ciudad destino | 🟨 | — |
| E | Transportadora | 🟨 lista | — |
| F | Conductor | 🟨 | — |
| G | Placa | 🟨 | — |
| H | Unidades enviadas | 🟨 | — |
| I | Valor del envío | 🟨 | — |
| J | Fecha promesa de entrega | 🟨 | — |
| K | Fecha de entrega real | 🟨 | — |
| L | Días en ruta | ⬜ | `=SI(O($A4="";$B4="");"";SI($K4<>"";$K4-$B4;HOY()-$B4))` |
| M | ¿Llegó a tiempo? | ⬜ | `=SI(O($A4="";$J4="");"";SI($K4="";SI(HOY()>$J4;"Atrasado";"En ruta");SI($K4<=$J4;"Sí";"No")))` |
| N | Novedades | ⬜ | `=SI($A4="";"";CONTAR.SI.CONJUNTO(NOVEDADES!$C$4:$C$1503;$A4))` |
| O | ¿Llegó completa? | ⬜ | `=SI($A4="";"";SI(CONTAR.SI.CONJUNTO(NOVEDADES!$C$4:$C$1503;$A4;NOVEDADES!$M$4:$M$1503;"SÍ")>0;"No";"Sí"))` |
| P | OTIF | ⬜ | `=SI(O($A4="";$K4="");"";SI(Y($M4="Sí";$O4="Sí");"OTIF";"Falló"))` |

> `Fecha promesa de entrega` es la columna que hace posible medir OTIF. Sin ella no hay indicador.

---

## Hoja `NOVEDADES`

26 columnas en cinco bloques. **Solo 11 se digitan.**

### ① Identificar el envío

| Col | Encabezado | Tipo | Fórmula |
|---|---|---|---|
| A | ID | ⬜ | `=SI($C4="";"";"N-"&TEXTO(FILA()-3;"0000"))` |
| B | Fecha de la novedad | 🟨 | — |
| **C** | **Nº Guía / Remisión** | 🟨 **LLAVE** | — |
| D | Validación | ⬜ | `=SI($C4="";"";SI(CONTAR.SI.CONJUNTO(ENVIOS!$A$4:$A$3003;$C4)=0;"NO EXISTE";SI(CONTAR.SI.CONJUNTO(ENVIOS!$A$4:$A$3003;$C4)>1;"DUPLICADA";"OK")))` |
| E | Cliente | ⬜ | `=SI($C4="";"";SI.ERROR(INDICE(ENVIOS!$C$4:$C$3003;COINCIDIR($C4;ENVIOS!$A$4:$A$3003;0));"—"))` |
| F | Ciudad destino | ⬜ | igual, con `ENVIOS!$D$4:$D$3003` |
| G | Transportadora | ⬜ | igual, con `ENVIOS!$E$4:$E$3003` |
| H | Conductor | ⬜ | igual, con `ENVIOS!$F$4:$F$3003` |
| I | Placa | ⬜ | igual, con `ENVIOS!$G$4:$G$3003` |
| J | Fecha despacho | ⬜ | igual, con `ENVIOS!$B$4:$B$3003` |

### ② Clasificar

| Col | Encabezado | Tipo | Fórmula |
|---|---|---|---|
| K | Tipo de novedad | 🟨 lista | — |
| L | Gravedad | ⬜ | `=SI($K4="";"";SI.ERROR(INDICE(CONFIG!$B$4:$B$43;COINCIDIR($K4;CONFIG!$A$4:$A$43;0));"Media"))` |
| M | ¿Afecta la entrega? | ⬜ | `=SI($K4="";"";SI.ERROR(INDICE(CONFIG!$D$4:$D$43;COINCIDIR($K4;CONFIG!$A$4:$A$43;0));"NO"))` |
| N | Causa raíz | 🟨 lista | — |
| O | Familia (6M) | ⬜ | `=SI($N4="";"";SI.ERROR(INDICE(CONFIG!$G$4:$G$43;COINCIDIR($N4;CONFIG!$F$4:$F$43;0));"Por definir"))` |
| P | Área responsable | ⬜ | `=SI($N4="";"";SI.ERROR(INDICE(CONFIG!$H$4:$H$43;COINCIDIR($N4;CONFIG!$F$4:$F$43;0));"Por definir"))` |

`¿Afecta la entrega?` es lo que alimenta el «in full» de OTIF: un sobrante o una factura mal
hecha son novedades, pero la entrega llegó completa.

### ③ Impacto

| Col | Encabezado | Tipo |
|---|---|---|
| Q | Unidades afectadas | 🟨 |
| R | Valor afectado | 🟨 |

### ④ Gestionar y cerrar

| Col | Encabezado | Tipo | Fórmula |
|---|---|---|---|
| S | Estado | 🟨 lista | — |
| T | Responsable | 🟨 lista | — |
| U | Fecha límite | ⬜ | `=SI(O($B4="";$K4="");"";DIA.LAB($B4;SI.ERROR(INDICE(CONFIG!$C$4:$C$43;COINCIDIR($K4;CONFIG!$A$4:$A$43;0));3)))` |
| V | Fecha de solución | 🟨 | — |
| W | Días abiertos | ⬜ | `=SI($B4="";"";SI($V4<>"";$V4-$B4;HOY()-$B4))` |
| X | Estado SLA | ⬜ | ver abajo |

```excel
=SI($C4="";"";SI(SI.ERROR(INDICE(CONFIG!$K$4:$K$43;COINCIDIR($S4;CONFIG!$J$4:$J$43;0));"NO")="SÍ";
  SI(O($V4="";$U4="");"Resuelta";SI($V4>$U4;"Resuelta tarde";"Resuelta a tiempo"));
  SI($U4="";"Sin clasificar";SI(HOY()>$U4;"Vencida";SI(HOY()>=$U4-1;"Por vencer";"En plazo")))))
```

No tiene ningún estado escrito a mano: lee la columna `¿CIERRA EL CASO?` de `CONFIG`.

| Valor | Significado |
|---|---|
| `En plazo` | Abierta, dentro del plazo |
| `Por vencer` | Vence hoy o mañana |
| `Vencida` | Se pasó del plazo y sigue abierta |
| `Resuelta a tiempo` | Cerrada dentro del plazo |
| `Resuelta tarde` | Cerrada fuera del plazo |
| `Resuelta` | Cerrada sin fecha de solución (falta dato) |
| `Sin clasificar` | Falta el tipo de novedad |

### ⑤ Constancia

| Col | Encabezado | Tipo |
|---|---|---|
| Y | Qué se hizo | 🟨 |
| Z | Notas / soporte | 🟨 |

---

## Hoja `CONFIG`

Todo el comportamiento del archivo se cambia aquí, sin tocar fórmulas.

| Rango | Contenido | Alimenta |
|---|---|---|
| `A4:D43` | Tipo de novedad · Gravedad · SLA (días hábiles) · ¿Afecta la entrega? | `NOVEDADES!K,L,M,U` |
| `F4:H43` | Causa raíz · Familia 6M · Área responsable | `NOVEDADES!N,O,P` |
| `J4:K43` | Estado · ¿Cierra el caso? | `NOVEDADES!S,X` |
| `M4:M43` | Transportadora | `ENVIOS!E` + scorecard |
| `O4:O43` | Responsable | `NOVEDADES!T` |
| `Q4:Q23` | Auxiliar del Pareto — no borrar | `TABLERO` |

### Tipos de novedad

| Tipo | Gravedad | SLA | ¿Afecta la entrega? |
|---|---|---|---|
| Vehículo varado / falla mecánica | Crítica | 1 | SÍ |
| Pérdida o robo de mercancía | Crítica | 1 | SÍ |
| Retraso en vía | Alta | 1 | NO |
| Cliente rechaza el envío | Alta | 2 | SÍ |
| Faltante (llegó de menos) | Alta | 2 | SÍ |
| Producto equivocado | Alta | 2 | SÍ |
| Pago contraentrega fallido | Alta | 2 | SÍ |
| Avería / producto dañado | Alta | 3 | SÍ |
| Producto vencido o próximo a vencer | Alta | 3 | SÍ |
| Cliente ausente / no atiende | Media | 2 | SÍ |
| Dirección errada o incompleta | Media | 2 | SÍ |
| Cliente cerrado / fuera de horario | Media | 2 | SÍ |
| Zona restringida o sin acceso | Media | 3 | SÍ |
| Empaque en mal estado | Media | 3 | NO |
| Soporte de entrega sin firmar | Media | 4 | NO |
| Error en factura o precio | Media | 5 | NO |
| Entrega parcial acordada | Baja | 5 | SÍ |
| Sobrante (llegó de más) | Baja | 5 | NO |
| Flete no liquidado | Baja | 5 | NO |

### Causas raíz (6M de Ishikawa)

| Causa raíz | Familia | Área |
|---|---|---|
| Error de alistamiento (picking) | Método | Bodega |
| Embalaje o estibado deficiente | Material | Bodega |
| Inventario descuadrado | Medición | Bodega |
| Manipulación brusca en cargue/descargue | Mano de obra | Transporte |
| Sobrecupo o mal acomodo en el vehículo | Método | Transporte |
| Conductor sin capacitación o procedimiento | Mano de obra | Transporte |
| Falla mecánica del vehículo | Máquina | Transporte |
| Ruta mal planeada o secuencia errada | Método | Planeación |
| Promesa de entrega irreal | Método | Planeación |
| Datos del cliente desactualizados | Medición | Comercial |
| Error de digitación del pedido | Mano de obra | Comercial |
| Cliente cambió de decisión | Externo | Comercial |
| Error en facturación o precio | Método | Facturación |
| Cliente sin cupo / cartera bloqueada | Método | Cartera |
| Producto con calidad o rotación deficiente | Material | Calidad |
| Tráfico, cierre vial u orden público | Medio ambiente | Externo |
| Clima adverso | Medio ambiente | Externo |
| Sin clasificar aún | Por definir | Por definir |

### Estados

| Estado | ¿Cierra? |
|---|---|
| Sin gestionar · En gestión · Esperando a la transportadora · Esperando al cliente | NO |
| Resuelta · Anulada | SÍ |

---

## Validación de datos

Los desplegables usan **nombres dinámicos**: al agregar una fila en `CONFIG` aparecen solos.

| Nombre | Fórmula |
|---|---|
| `TIPOS_NOVEDAD` | `=DESREF(CONFIG!$A$4;0;0;MAX(1;CONTARA(CONFIG!$A$4:$A$43));1)` |
| `CAUSAS_RAIZ` | `=DESREF(CONFIG!$F$4;0;0;MAX(1;CONTARA(CONFIG!$F$4:$F$43));1)` |
| `ESTADOS_NOVEDAD` | `=DESREF(CONFIG!$J$4;0;0;MAX(1;CONTARA(CONFIG!$J$4:$J$43));1)` |
| `TRANSPORTADORAS` | `=DESREF(CONFIG!$M$4;0;0;MAX(1;CONTARA(CONFIG!$M$4:$M$43));1)` |
| `RESPONSABLES` | `=DESREF(CONFIG!$O$4;0;0;MAX(1;CONTARA(CONFIG!$O$4:$O$43));1)` |

| Rango | Regla | Estilo |
|---|---|---|
| `NOVEDADES!K` / `N` / `S` / `T` | Lista | 🛑 Bloquea |
| `NOVEDADES!B` | Fecha entre 2020 y 2040 | 🛑 Bloquea |
| `NOVEDADES!V` | `=O($V4="";Y(ESNUMERO($V4);$V4>=$B4))` | 🛑 Bloquea |
| `NOVEDADES!Q` / `R` | Número ≥ 0 | 🛑 Bloquea |
| `ENVIOS!E` | Lista de transportadoras | ⚠️ Advierte |
| `ENVIOS!B` / `J` / `K` | Fecha válida | ⚠️ Advierte |
| `ENVIOS!H` / `I` | Número ≥ 0 | ⚠️ Advierte |

En `ENVIOS` la validación advierte pero no bloquea, para no interrumpir un pegado masivo.

---

## Formato condicional

| Hoja | Rango | Regla | Color |
|---|---|---|---|
| NOVEDADES | `X` Estado SLA | En plazo / Por vencer / Vencida | verde / ámbar / rojo |
| NOVEDADES | `X` | Resuelta a tiempo / tarde / sin fecha | azul / naranja / gris |
| NOVEDADES | `L` Gravedad | Crítica / Alta / Media / Baja | rojo sólido / rojo / ámbar / verde |
| NOVEDADES | `M` ¿Afecta la entrega? | `SÍ` | ámbar |
| NOVEDADES | `D` Validación | OK / NO EXISTE / DUPLICADA | verde / rojo / ámbar |
| NOVEDADES | `S` Estado | `Sin gestionar` → rojo; cierra=SÍ → verde; resto → ámbar (leído de `CONFIG`) | |
| NOVEDADES | `V` | `=Y($V4="";$X4="Resuelta")` — cerró sin fecha | rojo |
| NOVEDADES | `R`, `W` | Barra de datos | ámbar / gris |
| NOVEDADES | `A:Z` | `=$X4="Vencida"` → texto rojo en toda la fila | |
| ENVIOS | `M`, `O`, `P` | Sí / No / OTIF / Falló / En ruta / Atrasado | verde / rojo / gris |
| ENVIOS | `N` | `> 0` | ámbar |
| ENVIOS | `A:P` | Guía duplicada en la base | texto naranja |
| TABLERO | KPIs | OTIF ≥95% verde / <90% rojo · tasa >5% rojo · vencidas >0 rojo · SLA <90% rojo | |
| TABLERO | `M15:M24` | Nota A / B / C / D | verde / azul / ámbar / rojo |
| TABLERO | `F30:F41` | `% acumulado ≤ 80%` → resaltado: son las causas a atacar | ámbar |

El resaltado de fila vencida usa solo tipografía, no relleno, para no tapar el código de colores.

---

## Hoja `TABLERO`

Periodo en `E4` (Desde) y `G4` (Hasta). Abajo, `$PN` y `$PE` abrevian los criterios de periodo:

- `$PN` = `NOVEDADES!$B$4:$B$1503;">="&$E$4;NOVEDADES!$B$4:$B$1503;"<="&$G$4`
- `$PE` = `ENVIOS!$B$4:$B$3003;">="&$E$4;ENVIOS!$B$4:$B$3003;"<="&$G$4`
- `$ENTREGADOS` = `(CONTAR.SI.CONJUNTO(ENVIOS!$P$4:$P$3003;"OTIF";$PE)+CONTAR.SI.CONJUNTO(ENVIOS!$P$4:$P$3003;"Falló";$PE))`

### KPIs

| Celda | KPI | Fórmula |
|---|---|---|
| `D7` | **OTIF** | `=SI.ERROR(CONTAR.SI.CONJUNTO(ENVIOS!$P$4:$P$3003;"OTIF";$PE)/$ENTREGADOS;"—")` |
| `F7` | Entregas a tiempo | `=SI.ERROR(CONTAR.SI.CONJUNTO(ENVIOS!$M$4:$M$3003;"Sí";$PE)/$ENTREGADOS;"—")` |
| `H7` | **Tasa de novedades** | `=SI.ERROR(CONTAR.SI.CONJUNTO(ENVIOS!$N$4:$N$3003;">0";$PE)/CONTAR.SI.CONJUNTO($PE);"—")` |
| `J7` | Valor afectado | `=SUMAR.SI.CONJUNTO(NOVEDADES!$R$4:$R$1503;$PN)` |
| `L7` | Envíos del periodo | `=CONTAR.SI.CONJUNTO($PE)` |
| `D10` | Novedades | `=CONTAR.SI.CONJUNTO($PN)` |
| `F10` | Abiertas | `=CONTAR.SI.CONJUNTO(NOVEDADES!$X$4:$X$1503;"En plazo";$PN)+…"Por vencer"…+…"Vencida"…+…"Sin clasificar"…` |
| `H10` | Vencidas | `=CONTAR.SI.CONJUNTO(NOVEDADES!$X$4:$X$1503;"Vencida";$PN)` |
| `J10` | Días prom. de solución | `=SI.ERROR(REDONDEAR(PROMEDIO.SI.CONJUNTO(NOVEDADES!$W$4:$W$1503;$PN);1);0)` |
| `L10` | **Cumplimiento de SLA** | `=SI.ERROR(CONTAR.SI.CONJUNTO(NOVEDADES!$X$4:$X$1503;"Resuelta a tiempo";$PN)/CONTAR.SI.CONJUNTO(NOVEDADES!$X$4:$X$1503;"Resuelta*";$PN);"—")` |

**Por qué la tasa de novedades cuenta envíos y no novedades:** un envío puede generar tres
incidencias. Dividir novedades entre envíos daría un porcentaje inflado que puede pasar del 100%.
`ENVIOS!N` marca el envío una sola vez, así que responde la pregunta correcta: *de cada 100
envíos, ¿cuántos salieron mal?*

**Por qué el denominador de OTIF se cuenta como `OTIF + Falló`:** solo se puede evaluar un envío
ya entregado. Contarlo de forma explícita es más robusto que usar el criterio `"<>"` sobre la
fecha de entrega.

### Scorecard de transportadoras (filas 15-24)

| Col | Métrica | Fórmula (fila 15, `$e` = `ENVIOS!$E$4:$E$3003;$B15`, `$g` = `NOVEDADES!$G$4:$G$1503;$B15`) |
|---|---|---|
| B | Transportadora | `=SI(CONFIG!$M4="";"";CONFIG!$M4)` |
| D | Envíos | `=SI($B15="";"";CONTAR.SI.CONJUNTO($e;$PE))` |
| E | OTIF | `=SI($B15="";"";SI.ERROR(CONTAR.SI.CONJUNTO($e;ENVIOS!$P$4:$P$3003;"OTIF";$PE)/(CONTAR.SI.CONJUNTO($e;ENVIOS!$P$4:$P$3003;"OTIF";$PE)+CONTAR.SI.CONJUNTO($e;ENVIOS!$P$4:$P$3003;"Falló";$PE));"—"))` |
| F | Novedades | `=SI($B15="";"";CONTAR.SI.CONJUNTO($g;$PN))` |
| G | Tasa | `=SI($B15="";"";SI.ERROR(CONTAR.SI.CONJUNTO($e;ENVIOS!$N$4:$N$3003;">0";$PE)/$D15;"—"))` |
| H | Abiertas | suma de 4 `CONTAR.SI.CONJUNTO` sobre `NOVEDADES!$X` |
| I | Vencidas | `=SI($B15="";"";CONTAR.SI.CONJUNTO($g;NOVEDADES!$X$4:$X$1503;"Vencida";$PN))` |
| J | Días prom. | `=SI($B15="";"";SI.ERROR(REDONDEAR(PROMEDIO.SI.CONJUNTO(NOVEDADES!$W$4:$W$1503;$g;$PN);1);0))` |
| K | Valor afectado | `=SI($B15="";"";SUMAR.SI.CONJUNTO(NOVEDADES!$R$4:$R$1503;$g;$PN))` |
| L | **Puntaje** | `=SI(O($B15="";$D15=0;NO(ESNUMERO($E15)));"—";REDONDEAR($E15*60+(1-N($G15))*25+SI($F15=0;15;(1-$I15/$F15)*15);0))` |
| M | **Nota** | `=SI(NO(ESNUMERO($L15));"—";SI($L15>=90;"A";SI($L15>=80;"B";SI($L15>=70;"C";"D"))))` |

**Puntaje** = OTIF ×60 + (1 − tasa de novedades) ×25 + (1 − vencidas/novedades) ×15.
**Nota:** A ≥ 90 · B 80-89 · C 70-79 · D < 70.

### Pareto de causa raíz (filas 30-41)

Auxiliar en `CONFIG!Q4:Q23`:
`=SI($F4="";"";CONTAR.SI.CONJUNTO(NOVEDADES!$N$4:$N$1503;$F4;NOVEDADES!$B$4:$B$1503;">="&TABLERO!$E$4;NOVEDADES!$B$4:$B$1503;"<="&TABLERO!$G$4)+FILA()/100000)`

El `+FILA()/100000` es un desempate infinitesimal: sin él, dos causas con el mismo número de
casos harían que `COINCIDIR` devolviera siempre la misma y el ranking repetiría filas.

| Col | Fórmula (fila 30, puesto 1) |
|---|---|
| B | `=SI.ERROR(INDICE(CONFIG!$F$4:$F$23;COINCIDIR(K.ESIMO.MAYOR(CONFIG!$Q$4:$Q$23;1);CONFIG!$Q$4:$Q$23;0));"")` |
| D | `=SI($B30="";"";REDONDEAR.MENOS(K.ESIMO.MAYOR(CONFIG!$Q$4:$Q$23;1);0))` |
| E | `=SI($B30="";"";SI.ERROR($D30/$D$42;0))` |
| F | `=SI($B30="";"";SI.ERROR(SUMA($D$30:$D30)/$D$42;0))` |
| G | `=SI($B30="";"";SUMAR.SI.CONJUNTO(NOVEDADES!$R$4:$R$1503;NOVEDADES!$N$4:$N$1503;$B30;$PN))` |

En las filas 31 a 41 cambie el `1` de `K.ESIMO.MAYOR` por 2, 3, … 12.

### Gráficas

Cuatro gráficas nativas de Excel a la derecha de las tablas (columnas O a V). Se recalculan
solas con el periodo, porque leen las mismas celdas de las tablas.

| Gráfica | Lee | Ancla |
|---|---|---|
| OTIF por transportadora (columnas) | `B15:B24` × `E15:E24` | `O14` |
| Causas que más pesan (barras) | `B30:B41` × `D30:D41` | `O32` |
| Novedades por tipo (barras) | `B46:B64` × `D46:D64` | `O56` |
| Estado de la gestión (barras) | `B69:B74` × `D69:D74` | `O85` |

### Otras secciones

- **Novedades por tipo** (filas 46-64): casos, %, valor, gravedad, ¿afecta la entrega?, abiertas, vencidas, días prom.
- **Estado de la gestión** y **Familia 6M** (filas 69-77), lado a lado.
- **Buscador** (fila 80): se escribe la guía en `D80` y sale la ficha completa. Las últimas
  novedades usan `=BUSCAR(2;1/(NOVEDADES!$C$4:$C$1503=$D$80);NOVEDADES!$X$4:$X$1503)`, que
  devuelve la **última** coincidencia y no la primera.

---

## Verificación

Las fórmulas se evaluaron con un motor de cálculo independiente (`formulas`) sobre un libro
sembrado con 9 envíos y 9 novedades: **1.527 celdas calculadas, 0 errores**
(`#N/A`, `#REF!`, `#VALUE!`, `#DIV/0!`, `#NAME?`, `#NUM!`, `#NULL!`).

Resultados contrastados a mano: OTIF 3/7 = 42,9% · a tiempo 4/7 = 57,1% · tasa de novedades
6/9 = 66,7% · cumplimiento de SLA 2/3 = 66,7% · puntaje de Transportadora A = 0,5×60 +
0,5×25 + 1×15 = 58 → nota D. Detección de guía inexistente y duplicada, los siete valores del
semáforo SLA, el Pareto con su acumulado y el buscador con el campo vacío.

El archivo de ejemplo se verificó igual: 30 envíos y 14 novedades, **1.846 celdas calculadas,
0 errores**. Sus resultados: OTIF 67,9% · entregas a tiempo 71,4% · tasa de novedades 40,0% ·
cumplimiento de SLA 85,7%, y un scorecard que va de 97 puntos (nota A) a 38 (nota D).

El ejemplo incluye a propósito un envío que llegó puntual pero incompleto (`G-2426`), para que se
vea por qué «entregas a tiempo» (71,4%) es mayor que OTIF (67,9%): llegar a tiempo no basta.

Tres defectos encontrados y corregidos durante esa verificación:

1. El denominador de OTIF usaba `CONTAR.SI.CONJUNTO(rango;"<>")` para contar entregas hechas;
   el conteo salía mal y el OTIF daba 150%. Se reemplazó por la suma explícita de `OTIF` + `Falló`.
2. El mismo error en el OTIF por transportadora del scorecard.
3. El total del Pareto usaba el mismo criterio `"<>"` y daba 0, lo que dejaba todos los
   porcentajes en cero. Ahora es el total de novedades del periodo.

---

## Portabilidad

| | Excel 365 / 2021 | Excel 2010-2019 | Google Sheets |
|---|---|---|---|
| `ÍNDICE`+`COINCIDIR` | ✅ | ✅ | ✅ |
| `DIA.LAB` | ✅ | ✅ | ✅ |
| Nombres con `DESREF` | ✅ | ✅ | ❌ — apunte la validación al rango directo `CONFIG!A4:A43` |
| Comodín `"Resuelta*"` | ✅ | ✅ | ✅ |
| Formato condicional con referencia a otra hoja | ✅ | ✅ | ✅ |

El archivo usa `ÍNDICE`+`COINCIDIR` en vez de `BUSCARX` a propósito: funciona en cualquier
versión y no se rompe si se insertan columnas.

---

## Notas de operación

- Las hojas están protegidas **sin contraseña**: Revisar → Desproteger hoja y listo.
- Los plazos se cuentan en días hábiles. Para descontar festivos, agregue una columna de fechas
  en `CONFIG` y páselas como tercer argumento de `DIA.LAB`.
- Capacidad: 3.000 envíos y 1.500 novedades.
- El archivo de ejemplo es solo para mirar: trabaje sobre el archivo vacío.
- Antes de empezar, reemplace «Transportadora A, B, C» en `CONFIG!M` por los nombres reales.
