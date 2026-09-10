# Matriz de Novedades de Logística y Transporte — Arquitectura

Diseño completo de la matriz automatizada para control de eventos operativos, entregas
fallidas, devoluciones y gestión de transportadores. Construida sobre las convenciones ya
usadas en `CONTROL_DEVOLUCIONES_Y_CUMPLIDOS_GESTOAGRO.xlsx`.

**Archivo listo para usar:** `MATRIZ_NOVEDADES_LOGISTICA_GESTOAGRO.xlsx`
**Generador reproducible:** `generar_matriz.py` (requiere `openpyxl`)

---

## 0. Convención de colores (regla de oro)

| Color | Significado | Encabezado |
|---|---|---|
| 🟨 Amarillo `#FFF2CC` | Celda de **captura manual** | Dorado `#BF8F00` |
| ⬜ Gris `#F2F2F2` | Celda **calculada** — no se toca | Azul `#2E75B6` |
| 🟩 Verde `#1F4E2E` | Título / sección | — |

Las hojas `DESPACHOS`, `NOVEDADES` y `DASHBOARD` están protegidas con **PIN 2026**: solo las
celdas amarillas se editan. `LISTAS` queda libre para ampliar catálogos.

> **Nota de sintaxis.** Las fórmulas se muestran en **español con `;`** como separador de
> argumentos. Si su Excel usa `,`, reemplace `;` por `,`. La versión inglesa de cada fórmula
> (la que realmente queda guardada en el archivo `.xlsx`) es equivalente 1 a 1.

---

## 1. Estructura modular de pestañas

| Orden | Pestaña | Rol | Fila de encabezado | Datos desde | Capacidad |
|---|---|---|---|---|---|
| 1 | `GUÍA` | Instructivo de uso y cierre | — | — | — |
| 2 | `DASHBOARD` | Indicadores consolidados | — | — | — |
| 3 | `NOVEDADES` | Registro de incidencias | 3 | 4 | 2.000 novedades |
| 4 | `DESPACHOS` | Hoja maestra (base) | 2 | 3 | 3.000 despachos |
| 5 | `LISTAS` | Catálogos y reglas de negocio | 2 | 3 | 40 ítems por catálogo |

**Llave de cruce:** `# Pedido / Remisión`. Vive en `DESPACHOS!B` y se digita en `NOVEDADES!C`.

---

## 2. Hoja `DESPACHOS` (base maestra)

Las columnas **A a J** conservan el orden exacto del export de Access: se pega tal cual desde
la fila 3. Las columnas **K, L y M** se completan a mano. **N y O** se calculan.

| Col | Encabezado | Tipo | Formato | Fórmula (español) |
|---|---|---|---|---|
| A | `# Planilla` | 🟨 Manual (pegar) | General | — |
| **B** | **`# Pedido / Remisión`** | 🟨 Manual (pegar) · **LLAVE** | General | — |
| C | `# Factura` | 🟨 Manual (pegar) | General | — |
| D | `Cliente` | 🟨 Manual (pegar) | General | — |
| E | `Peso KG` | 🟨 Manual (pegar) | `#,##0.0` | — |
| F | `Transportadora` | 🟨 Manual (pegar) | General | — |
| G | `Transportador` | 🟨 Manual (pegar) | General | — |
| H | `Placa` | 🟨 Manual (pegar) | General | — |
| I | `Ruta` | 🟨 Manual (pegar) | General | — |
| J | `Fecha despacho` | 🟨 Manual (pegar) | `dd/mm/aaaa` | — |
| K | `Destino / Ciudad` | 🟨 Manual | General | — |
| L | `Cajas enviadas` | 🟨 Manual | `#,##0` | — |
| M | `Valor despachado` | 🟨 Manual | `$#,##0` | — |
| N | `Zona SLA` | ⬜ Calculada | General | ver N3 |
| O | `¿Tiene novedad?` | ⬜ Calculada | General | ver O3 |

**N3 — Zona SLA** (clasifica cercana vs. nacional buscando la ruta/destino en el catálogo de zonas):

```excel
=SI($B3="";"";SI(SUMAPRODUCTO((LISTAS!$O$3:$O$42<>"")*ESNUMERO(HALLAR(LISTAS!$O$3:$O$42;$I3&" "&$K3)))>0;"CERCANA";"NACIONAL"))
```

**O3 — ¿Tiene novedad?** (contador inverso: marca qué despachos tienen incidencias):

```excel
=SI($B3="";"";SI(CONTAR.SI.CONJUNTO(NOVEDADES!$C$4:$C$2003;$B3)=0;"—";"SÍ ("&CONTAR.SI.CONJUNTO(NOVEDADES!$C$4:$C$2003;$B3)&")"))
```

Ambas se copian de la fila 3 hacia abajo. `O` es la base del **Ratio de Incidencia** real
(pedidos afectados, no novedades) del dashboard.

---

## 3. Hoja `NOVEDADES` (matriz principal)

**Solo se digitan 10 columnas.** Al escribir el `# Pedido` en `C`, se traen 7 campos desde
`DESPACHOS` y 3 más desde `LISTAS`.

| Col | Encabezado | Tipo | Formato | Fórmula (español) |
|---|---|---|---|---|
| A | `Consecutivo` | ⬜ Calculada | General | `=SI($C4="";"";"NOV-"&TEXTO(FILA()-3;"0000"))` |
| B | `Fecha novedad` | 🟨 Manual | `dd/mm/aaaa` | — |
| **C** | **`# Pedido / Remisión`** | 🟨 Manual · **LLAVE** | General | — |
| D | `Cliente` | ⬜ Calculada | General | `=SI($C4="";"";SI.ERROR(INDICE(DESPACHOS!$D$3:$D$3002;COINCIDIR($C4;DESPACHOS!$B$3:$B$3002;0));"SIN DESPACHO"))` |
| E | `Destino / Ciudad` | ⬜ Calculada | General | `=SI($C4="";"";SI.ERROR(INDICE(DESPACHOS!$K$3:$K$3002;COINCIDIR($C4;DESPACHOS!$B$3:$B$3002;0));""))` |
| F | `Ruta` | ⬜ Calculada | General | `=SI($C4="";"";SI.ERROR(INDICE(DESPACHOS!$I$3:$I$3002;COINCIDIR($C4;DESPACHOS!$B$3:$B$3002;0));""))` |
| G | `Transportadora` | ⬜ Calculada | General | `=SI($C4="";"";SI.ERROR(INDICE(DESPACHOS!$F$3:$F$3002;COINCIDIR($C4;DESPACHOS!$B$3:$B$3002;0));""))` |
| H | `Transportador` | ⬜ Calculada | General | `=SI($C4="";"";SI.ERROR(INDICE(DESPACHOS!$G$3:$G$3002;COINCIDIR($C4;DESPACHOS!$B$3:$B$3002;0));""))` |
| I | `Placa` | ⬜ Calculada | General | `=SI($C4="";"";SI.ERROR(INDICE(DESPACHOS!$H$3:$H$3002;COINCIDIR($C4;DESPACHOS!$B$3:$B$3002;0));""))` |
| J | `Fecha despacho` | ⬜ Calculada | `dd/mm/aaaa` | `=SI($C4="";"";SI.ERROR(INDICE(DESPACHOS!$J$3:$J$3002;COINCIDIR($C4;DESPACHOS!$B$3:$B$3002;0));""))` |
| K | `Verif. despacho` | ⬜ Calculada | General | ver K4 |
| L | `Tipo de novedad` | 🟨 Manual · lista | General | — |
| M | `Causa raíz` | 🟨 Manual · lista | General | — |
| N | `Área responsable` | ⬜ Calculada | General | `=SI($M4="";"";SI.ERROR(INDICE(LISTAS!$F$3:$F$42;COINCIDIR($M4;LISTAS!$E$3:$E$42;0));"Por definir"))` |
| O | `Responsable` | 🟨 Manual · lista | General | — |
| P | `Criticidad` | ⬜ Calculada | General | `=SI($L4="";"";SI.ERROR(INDICE(LISTAS!$B$3:$B$42;COINCIDIR($L4;LISTAS!$A$3:$A$42;0));"Media"))` |
| Q | `Cajas afectadas` | 🟨 Manual | `#,##0` | — |
| R | `Valor afectado` | 🟨 Manual | `$#,##0` | — |
| S | `% del despacho` | ⬜ Calculada | `0,0%` | ver S4 |
| T | `Estado` | 🟨 Manual · lista | General | — |
| U | `Fecha compromiso` | ⬜ Calculada | `dd/mm/aaaa` | ver U4 |
| V | `Fecha cierre real` | 🟨 Manual | `dd/mm/aaaa` | — |
| W | `Días de gestión` | ⬜ Calculada | `#,##0` | ver W4 |
| X | `Días de mora` | ⬜ Calculada | `#,##0` | ver X4 |
| Y | `Semáforo SLA` | ⬜ Calculada | General | ver Y4 |
| Z | `Acción correctiva` | 🟨 Manual | General | — |
| AA | `Observaciones` | 🟨 Manual | General | — |
| AB | `Soporte / evidencia` | 🟨 Manual | General | — |

### 3.1 Variante `BUSCARX` de las columnas D a J

Idéntico resultado, sintaxis más corta (Excel 365 / 2021 en adelante; **no existe en Google Sheets**):

```excel
=SI($C4="";"";SI.ERROR(BUSCARX($C4;DESPACHOS!$B$3:$B$3002;DESPACHOS!$D$3:$D$3002);"SIN DESPACHO"))
```

El archivo entregado usa `ÍNDICE`+`COINCIDIR` por compatibilidad total (Excel 2010+, Google
Sheets, LibreOffice) y porque no se rompe si se insertan columnas en `DESPACHOS`.

### 3.2 Fórmulas de control y SLA

**K4 — Verificación de la llave** (blinda el cruce contra pedidos inexistentes o duplicados):

```excel
=SI($C4="";"";SI(CONTAR.SI.CONJUNTO(DESPACHOS!$B$3:$B$3002;$C4)=0;"NO EXISTE";SI(CONTAR.SI.CONJUNTO(DESPACHOS!$B$3:$B$3002;$C4)>1;"DUPLICADO";"OK")))
```

**S4 — % del despacho afectado**:

```excel
=SI.ERROR(SI(O($R4="";$C4="");"";$R4/INDICE(DESPACHOS!$M$3:$M$3002;COINCIDIR($C4;DESPACHOS!$B$3:$B$3002;0)));"")
```

**U4 — Fecha compromiso** (SLA en días **hábiles** según el tipo de novedad, tomado de `LISTAS!C`):

```excel
=SI(O($B4="";$L4="");"";DIA.LAB($B4;SI.ERROR(INDICE(LISTAS!$C$3:$C$42;COINCIDIR($L4;LISTAS!$A$3:$A$42;0));3)))
```

> **Variante con festivos colombianos.** Cree en `LISTAS` una columna `S` con las fechas de los
> festivos del año y cambie la fórmula por:
> `=SI(O($B4="";$L4="");"";DIA.LAB($B4;SI.ERROR(INDICE(LISTAS!$C$3:$C$42;COINCIDIR($L4;LISTAS!$A$3:$A$42;0));3);LISTAS!$S$3:$S$25))`
> Si prefiere días calendario en vez de hábiles, use `$B4 + SI.ERROR(INDICE(...);3)`.

**W4 — Días de gestión** (corre mientras esté abierta; se congela al escribir la fecha de cierre):

```excel
=SI($B4="";"";SI($V4<>"";$V4-$B4;HOY()-$B4))
```

**X4 — Días de mora** (solo lo que excede la fecha compromiso; nunca negativo):

```excel
=SI(O($B4="";$U4="");"";SI($V4<>"";MAX(0;$V4-$U4);MAX(0;HOY()-$U4)))
```

**Y4 — Semáforo SLA / Estado de cierre** (el corazón de la matriz):

```excel
=SI($C4="";"";SI(SI.ERROR(INDICE(LISTAS!$I$3:$I$42;COINCIDIR($T4;LISTAS!$H$3:$H$42;0));"NO")="SÍ";SI(N($X4)>0;"CERRADA FUERA DE SLA";"CERRADA EN SLA");SI($U4="";"SIN CLASIFICAR";SI(N($X4)>0;"VENCIDA";SI(HOY()>=$U4-1;"POR VENCER";"EN PLAZO")))))
```

La lógica **no tiene estados escritos a mano**: lee la columna `¿CIERRA?` de `LISTAS`, así que
agregar un estado nuevo no obliga a tocar ninguna fórmula.

| Valor de `Y` | Significado |
|---|---|
| `EN PLAZO` | Abierta, dentro de la fecha compromiso |
| `POR VENCER` | Abierta, vence hoy o mañana |
| `VENCIDA` | Abierta y ya pasó la fecha compromiso |
| `CERRADA EN SLA` | Resuelta a tiempo |
| `CERRADA FUERA DE SLA` | Resuelta tarde |
| `SIN CLASIFICAR` | Falta el `Tipo de novedad` |

---

## 4. Hoja `LISTAS` — catálogos y reglas de negocio

Toda la parametrización del sistema vive aquí. **Agregar filas hacia abajo basta**: las listas
desplegables son dinámicas y crecen solas.

| Rango | Contenido | Alimenta |
|---|---|---|
| `A3:A42` | Tipo de novedad | Desplegable `NOVEDADES!L` |
| `B3:B42` | Criticidad (Alta/Media/Baja) | Cálculo `NOVEDADES!P` |
| `C3:C42` | SLA en días hábiles | Cálculo `NOVEDADES!U` |
| `E3:E42` | Causa raíz | Desplegable `NOVEDADES!M` |
| `F3:F42` | Área responsable | Cálculo `NOVEDADES!N` |
| `H3:H42` | Estado | Desplegable `NOVEDADES!T` |
| `I3:I42` | ¿Cierra? (SÍ/NO) | Cálculo `NOVEDADES!Y` |
| `K3:K42` | Transportadora | Desplegable `DESPACHOS!F` + tabla 4 del dashboard |
| `M3:M42` | Responsable | Desplegable `NOVEDADES!O` |
| `O3:O42` | Zona cercana | Cálculo `DESPACHOS!N` |

### 4.1 Tipo de novedad → criticidad → SLA

| Tipo de novedad | Criticidad | SLA (días hábiles) |
|---|---|---|
| Avería / producto dañado en transporte | Alta | 3 |
| Devolución parcial | Media | 3 |
| Rechazo total del pedido | Alta | 2 |
| Faltante en la entrega | Alta | 2 |
| Sobrante en la entrega | Baja | 5 |
| Producto equivocado | Alta | 2 |
| Producto vencido o próximo a vencer | Alta | 3 |
| Empaque en mal estado | Media | 3 |
| Retraso en vía / entrega tardía | Alta | 1 |
| Cliente cerrado / no ubicado | Media | 2 |
| Cliente rechaza / no recibe | Media | 2 |
| Dirección errada | Media | 2 |
| Vehículo varado / falla mecánica | Alta | 1 |
| Cobro pendiente / flete no liquidado | Media | 5 |
| Cumplido / soporte no entregado | Media | 4 |
| Diferencia en facturación o precio | Media | 5 |

### 4.2 Causa raíz → área responsable

| Causa raíz | Área responsable |
|---|---|
| Manipulación en cargue / descargue | Transporte |
| Estibado o embalaje deficiente | Bodega |
| Error de alistamiento (picking) | Bodega |
| Sobrecupo o mal acomodo en vehículo | Transporte |
| Demora del transportador | Transporte |
| Falla mecánica del vehículo | Transporte |
| Ruta mal programada | Logística |
| Error de digitación del pedido | Comercial |
| Error en facturación | Facturación |
| Dirección desactualizada en maestro | Comercial |
| Cliente sin cupo / cartera bloqueada | Cartera |
| Cliente no disponible / fuera de horario | Comercial |
| Producto con baja rotación / vencido | Calidad |
| Acuerdo comercial con el cliente | Comercial |
| Tráfico, cierre vial u orden público | Externo |
| Clima adverso | Externo |
| Sin causa asignada | Por definir |

### 4.3 Estados y regla de cierre

| Estado | ¿Cierra? | Efecto |
|---|---|---|
| Pendiente | NO | Cuenta como abierta, sigue sumando días |
| En gestión | NO | Abierta |
| En tránsito (retorno) | NO | Abierta |
| Recibida en bodega | NO | Abierta |
| En inspección | NO | Abierta |
| Escalada a transportadora | NO | Abierta |
| Pendiente nota crédito | NO | Abierta |
| Resuelto / Cerrado | SÍ | Cierra, congela días de gestión |
| Cerrada sin costo | SÍ | Cierra |
| Anulada | SÍ | Cierra |

---

## 5. Validación de datos

Los desplegables apuntan a **nombres definidos dinámicos**, no a rangos fijos: si mañana se
agrega un tipo de novedad en `LISTAS`, aparece solo en el desplegable sin reconfigurar nada.

| Nombre definido | Fórmula (Fórmulas → Administrador de nombres) |
|---|---|
| `TIPOS_NOVEDAD` | `=DESREF(LISTAS!$A$3;0;0;MAX(1;CONTARA(LISTAS!$A$3:$A$42));1)` |
| `CAUSAS_RAIZ` | `=DESREF(LISTAS!$E$3;0;0;MAX(1;CONTARA(LISTAS!$E$3:$E$42));1)` |
| `ESTADOS_NOV` | `=DESREF(LISTAS!$H$3;0;0;MAX(1;CONTARA(LISTAS!$H$3:$H$42));1)` |
| `TRANSPORTADORAS` | `=DESREF(LISTAS!$K$3;0;0;MAX(1;CONTARA(LISTAS!$K$3:$K$42));1)` |
| `RESPONSABLES` | `=DESREF(LISTAS!$M$3;0;0;MAX(1;CONTARA(LISTAS!$M$3:$M$42));1)` |

| Hoja | Rango | Tipo | Criterio | Estilo | Mensaje de error |
|---|---|---|---|---|---|
| NOVEDADES | `L4:L2003` | Lista | `=TIPOS_NOVEDAD` | 🛑 Bloquea | «Elija un tipo de la lista. Para agregar uno nuevo vaya a LISTAS columna A.» |
| NOVEDADES | `M4:M2003` | Lista | `=CAUSAS_RAIZ` | 🛑 Bloquea | «Elija una causa de la lista…» |
| NOVEDADES | `O4:O2003` | Lista | `=RESPONSABLES` | 🛑 Bloquea | «Elija de la lista (LISTAS columna M).» |
| NOVEDADES | `T4:T2003` | Lista | `=ESTADOS_NOV` | 🛑 Bloquea | «Elija un estado de la lista…» |
| NOVEDADES | `B4:B2003` | Fecha | entre `FECHA(2020;1;1)` y `FECHA(2035;12;31)` | 🛑 Bloquea | «Escriba una fecha real (dd/mm/aaaa).» |
| NOVEDADES | `V4:V2003` | Personalizada | `=O($V4="";Y(ESNUMERO($V4);$V4>=$B4))` | 🛑 Bloquea | «La fecha de cierre no puede ser anterior a la fecha de la novedad.» |
| NOVEDADES | `Q4:Q2003` | Decimal | `>= 0` | 🛑 Bloquea | «Debe ser un número mayor o igual a 0.» |
| NOVEDADES | `R4:R2003` | Decimal | `>= 0` | 🛑 Bloquea | «Debe ser un número mayor o igual a 0.» |
| DESPACHOS | `F3:F3002` | Lista | `=TRANSPORTADORAS` | ⚠️ Advierte | «No está en LISTAS. Si es correcta, agréguela en LISTAS columna K.» |
| DESPACHOS | `J3:J3002` | Fecha | entre `FECHA(2020;1;1)` y `FECHA(2035;12;31)` | ⚠️ Advierte | «Escriba una fecha real.» |
| DESPACHOS | `L3:M3002` | Decimal | `>= 0` | ⚠️ Advierte | — |

En `DESPACHOS` la validación es **de advertencia, no de bloqueo**, porque esa hoja se alimenta
pegando desde Access y un bloqueo interrumpiría el pegado.

---

## 6. Formato condicional

### 6.1 Hoja `NOVEDADES`

| # | Rango | Regla | Formato |
|---|---|---|---|
| 1 | `Y4:Y2003` | Valor de celda = `"VENCIDA"` | Fondo rojo `#FFC7CE`, texto `#9C0006` negrita |
| 2 | `Y4:Y2003` | = `"POR VENCER"` | Fondo ámbar `#FFEB9C`, texto `#9C6500` |
| 3 | `Y4:Y2003` | = `"EN PLAZO"` | Fondo verde `#C6EFCE`, texto `#006100` |
| 4 | `Y4:Y2003` | = `"CERRADA EN SLA"` | Fondo azul `#DDEBF7`, texto `#1F4E79` |
| 5 | `Y4:Y2003` | = `"CERRADA FUERA DE SLA"` | Fondo naranja `#F8CBAD`, texto `#833C00` |
| 6 | `Y4:Y2003` | = `"SIN CLASIFICAR"` | Fondo gris `#D9D9D9` |
| 7 | `P4:P2003` | = `"Alta"` / `"Media"` / `"Baja"` | Rojo / ámbar / verde |
| 8 | `T4:T2003` | `=$T4="Pendiente"` | Rojo |
| 9 | `T4:T2003` | `=Y($T4<>"";SI.ERROR(INDICE(LISTAS!$I$3:$I$42;COINCIDIR($T4;LISTAS!$H$3:$H$42;0));"NO")="SÍ")` | Verde |
| 10 | `T4:T2003` | `=Y($T4<>"";SI.ERROR(INDICE(LISTAS!$I$3:$I$42;COINCIDIR($T4;LISTAS!$H$3:$H$42;0));"NO")="NO")` | Ámbar |
| 11 | `K4:K2003` | `=O($K4="NO EXISTE";$K4="DUPLICADO")` | Rojo negrita |
| 12 | `X4:X2003` | Valor de celda `> 0` | Rojo negrita |
| 13 | `V4:V2003` | `=Y($V4="";IZQUIERDA($Y4;7)="CERRADA")` | Rojo — *cerrada sin fecha de cierre* |
| 14 | `R4:R2003` | Barra de datos (0 → percentil 95) | Barra dorada |
| 15 | `A4:AB2003` | `=$Y4="VENCIDA"` | Texto rojo negrita en **toda la fila** |

La regla 15 usa solo tipografía (no relleno) a propósito: así el resaltado de fila vencida no
tapa el código de colores amarillo/gris.

Las reglas 8, 9 y 10 se leen desde `LISTAS`: no hay estados escritos dentro del formato
condicional, salvo `"Pendiente"` que siempre debe verse en rojo.

### 6.2 Hoja `DESPACHOS`

| Rango | Regla | Formato |
|---|---|---|
| `O3:O3002` | `=IZQUIERDA($O3;2)="SÍ"` | Ámbar negrita |
| `A3:O3002` | `=Y($B3<>"";CONTAR.SI.CONJUNTO($B$3:$B$3002;$B3)>1)` | Texto naranja — *pedido duplicado en la base* |

### 6.3 Hoja `DASHBOARD`

| Celda | Regla | Formato |
|---|---|---|
| `F7` (% incidencia) | `> 5%` / `<= 3%` | Rojo / verde |
| `H7` (abiertas) | `> 0` | Ámbar |
| `H10` (vencidas) | `> 0` | Rojo |
| `J10` (% cumplimiento SLA) | `< 90%` / `>= 90%` | Rojo / verde |
| `C14:C30`, `C43:C58` | Barra de datos | Azul |
| `E63:E72` (% incidencia por transportadora) | `> 5%` | Rojo |
| `G63:G72` (vencidas) | `> 0` | Rojo |
| `I63:I72` (% cierre) | `< 80%` | Ámbar |

---

## 7. Hoja `DASHBOARD` — métricas y KPIs

Todo el tablero se filtra por el **periodo** en `E4` (Desde) y `G4` (Hasta), ambas amarillas.
Novedades se filtran por `Fecha novedad`; despachos por `Fecha despacho`.

### 7.1 Tarjetas de KPI

| Celda | KPI | Formato | Fórmula (español) |
|---|---|---|---|
| `B7` | Novedades del periodo | `#,##0` | `=CONTAR.SI.CONJUNTO(NOVEDADES!$B$4:$B$2003;">="&$E$4;NOVEDADES!$B$4:$B$2003;"<="&$G$4)` |
| `D7` | Pedidos despachados | `#,##0` | `=CONTAR.SI.CONJUNTO(DESPACHOS!$J$3:$J$3002;">="&$E$4;DESPACHOS!$J$3:$J$3002;"<="&$G$4)` |
| `F7` | **% Ratio de incidencia** | `0,0%` | `=SI.ERROR(CONTAR.SI.CONJUNTO(DESPACHOS!$J$3:$J$3002;">="&$E$4;DESPACHOS!$J$3:$J$3002;"<="&$G$4;DESPACHOS!$O$3:$O$3002;"SÍ*")/CONTAR.SI.CONJUNTO(DESPACHOS!$J$3:$J$3002;">="&$E$4;DESPACHOS!$J$3:$J$3002;"<="&$G$4);0)` |
| `H7` | Novedades abiertas | `#,##0` | `=CONTAR.SI.CONJUNTO(NOVEDADES!$Y$4:$Y$2003;"EN PLAZO";$P)+CONTAR.SI.CONJUNTO(NOVEDADES!$Y$4:$Y$2003;"POR VENCER";$P)+CONTAR.SI.CONJUNTO(NOVEDADES!$Y$4:$Y$2003;"VENCIDA";$P)+CONTAR.SI.CONJUNTO(NOVEDADES!$Y$4:$Y$2003;"SIN CLASIFICAR";$P)` |
| `J7` | Novedades cerradas | `#,##0` | `=CONTAR.SI.CONJUNTO(NOVEDADES!$Y$4:$Y$2003;"CERRADA*";$P)` |
| `B10` | Valor impactado | `$#,##0` | `=SUMAR.SI.CONJUNTO(NOVEDADES!$R$4:$R$2003;$P)` |
| `D10` | Cajas afectadas | `#,##0` | `=SUMAR.SI.CONJUNTO(NOVEDADES!$Q$4:$Q$2003;$P)` |
| `F10` | Días prom. de gestión | `#,##0.0` | `=SI.ERROR(REDONDEAR(PROMEDIO.SI.CONJUNTO(NOVEDADES!$W$4:$W$2003;$P);1);0)` |
| `H10` | Vencidas (SLA roto) | `#,##0` | `=CONTAR.SI.CONJUNTO(NOVEDADES!$Y$4:$Y$2003;"VENCIDA";$P)` |
| `J10` | % Cumplimiento SLA | `0,0%` | `=SI.ERROR(CONTAR.SI.CONJUNTO(NOVEDADES!$Y$4:$Y$2003;"CERRADA EN SLA";$P)/CONTAR.SI.CONJUNTO(NOVEDADES!$Y$4:$Y$2003;"CERRADA*";$P);"—")` |

> `$P` es la abreviatura de este par de criterios de periodo, que se repite en cada fórmula:
> `NOVEDADES!$B$4:$B$2003;">="&$E$4;NOVEDADES!$B$4:$B$2003;"<="&$G$4`

**Por qué el ratio de incidencia se calcula sobre `DESPACHOS!O` y no sobre el conteo de
novedades:** un mismo pedido puede generar 3 novedades. Dividir novedades entre despachos daría
un porcentaje inflado y podría superar el 100%. `DESPACHOS!O` marca el pedido una sola vez, así
que `F7` responde la pregunta correcta: *de cada 100 pedidos que despacho, ¿cuántos salen mal?*

### 7.2 Tabla 1 — Causa raíz (filas 14 a 30, total en 31)

| Col | Encabezado | Fórmula (fila 14; `LISTAS` fila 3) |
|---|---|---|
| B | Causa raíz | `=SI(LISTAS!$E3="";"";LISTAS!$E3)` |
| C | # Novedades | `=SI($B14="";"";CONTAR.SI.CONJUNTO(NOVEDADES!$M$4:$M$2003;$B14;$P))` |
| D | % Participación | `=SI($B14="";"";SI.ERROR($C14/$C$31;0))` |
| E | Valor impactado | `=SI($B14="";"";SUMAR.SI.CONJUNTO(NOVEDADES!$R$4:$R$2003;NOVEDADES!$M$4:$M$2003;$B14;$P))` |
| F | Orden (auxiliar) | `=SI($B14="";"";$C14+FILA()/100000)` |

La columna `F` añade un desempate infinitesimal al conteo. Sin ella, dos causas con el mismo
número de casos harían que `COINCIDIR` devolviera siempre la misma y el Top 5 mostraría la
misma causa repetida.

### 7.3 Tabla 2 — Top 5 causas raíz (filas 35 a 39)

| Col | Encabezado | Fórmula (fila 35, puesto 1) |
|---|---|---|
| B | Puesto | `="#"&1` |
| C | Causa raíz | `=SI.ERROR(INDICE($B$14:$B$30;COINCIDIR(K.ESIMO.MAYOR($F$14:$F$30;1);$F$14:$F$30;0));"—")` |
| D | # Novedades | `=SI.ERROR(INDICE($C$14:$C$30;COINCIDIR(K.ESIMO.MAYOR($F$14:$F$30;1);$F$14:$F$30;0));0)` |
| E | % Participación | `=SI.ERROR($D35/$C$31;0)` |

En las filas 36 a 39 cambie el `1` de `K.ESIMO.MAYOR` por 2, 3, 4 y 5. El ranking se reordena
solo al cambiar el periodo.

### 7.4 Tabla 3 — Novedades por tipo (filas 43 a 58, total en 59)

| Col | Encabezado | Fórmula (fila 43) |
|---|---|---|
| B | Tipo de novedad | `=SI(LISTAS!$A3="";"";LISTAS!$A3)` |
| C | # Novedades | `=SI($B43="";"";CONTAR.SI.CONJUNTO(NOVEDADES!$L$4:$L$2003;$B43;$P))` |
| D | % Part. | `=SI($B43="";"";SI.ERROR($C43/$C$59;0))` |
| E | Valor impactado | `=SI($B43="";"";SUMAR.SI.CONJUNTO(NOVEDADES!$R$4:$R$2003;NOVEDADES!$L$4:$L$2003;$B43;$P))` |
| F | Abiertas | `=SI($B43="";"";CONTAR.SI.CONJUNTO(NOVEDADES!$Y$4:$Y$2003;"EN PLAZO";NOVEDADES!$L$4:$L$2003;$B43;$P)+ …"POR VENCER"… + …"VENCIDA"… + …"SIN CLASIFICAR"…)` |
| G | Cerradas | `=SI($B43="";"";CONTAR.SI.CONJUNTO(NOVEDADES!$L$4:$L$2003;$B43;NOVEDADES!$Y$4:$Y$2003;"CERRADA*";$P))` |
| H | Vencidas | `=SI($B43="";"";CONTAR.SI.CONJUNTO(NOVEDADES!$L$4:$L$2003;$B43;NOVEDADES!$Y$4:$Y$2003;"VENCIDA";$P))` |

### 7.5 Tabla 4 — Abiertas vs. cerradas por transportadora (filas 63 a 72, total en 73)

| Col | Encabezado | Fórmula (fila 63) |
|---|---|---|
| B | Transportadora | `=SI(LISTAS!$K3="";"";LISTAS!$K3)` |
| C | Despachos | `=SI($B63="";"";CONTAR.SI.CONJUNTO(DESPACHOS!$F$3:$F$3002;$B63;DESPACHOS!$J$3:$J$3002;">="&$E$4;DESPACHOS!$J$3:$J$3002;"<="&$G$4))` |
| D | Novedades | `=SI($B63="";"";CONTAR.SI.CONJUNTO(NOVEDADES!$G$4:$G$2003;$B63;$P))` |
| E | % Incidencia | `=SI($B63="";"";SI.ERROR($D63/$C63;"—"))` |
| F | Abiertas | `=SI($B63="";"";CONTAR.SI.CONJUNTO(NOVEDADES!$Y$4:$Y$2003;"EN PLAZO";NOVEDADES!$G$4:$G$2003;$B63;$P)+ …"POR VENCER"… + …"VENCIDA"… + …"SIN CLASIFICAR"…)` |
| G | Vencidas | `=SI($B63="";"";CONTAR.SI.CONJUNTO(NOVEDADES!$G$4:$G$2003;$B63;NOVEDADES!$Y$4:$Y$2003;"VENCIDA";$P))` |
| H | Cerradas | `=SI($B63="";"";CONTAR.SI.CONJUNTO(NOVEDADES!$G$4:$G$2003;$B63;NOVEDADES!$Y$4:$Y$2003;"CERRADA*";$P))` |
| I | % Cierre | `=SI($B63="";"";SI.ERROR($H63/$D63;"—"))` |
| J | Días prom. | `=SI($B63="";"";SI.ERROR(REDONDEAR(PROMEDIO.SI.CONJUNTO(NOVEDADES!$W$4:$W$2003;NOVEDADES!$G$4:$G$2003;$B63;$P);1);0))` |
| K | Valor impactado | `=SI($B63="";"";SUMAR.SI.CONJUNTO(NOVEDADES!$R$4:$R$2003;NOVEDADES!$G$4:$G$2003;$B63;$P))` |

Esta es la tabla de **negociación con el transportador**: incidencia, mora y plata en una sola
línea por empresa.

### 7.6 Tabla 5 — Pipeline por estado (filas 77 a 86, total en 87)

| Col | Encabezado | Fórmula (fila 77) |
|---|---|---|
| B | Estado | `=SI(LISTAS!$H3="";"";LISTAS!$H3)` |
| C | # Casos | `=SI($B77="";"";CONTAR.SI.CONJUNTO(NOVEDADES!$T$4:$T$2003;$B77;$P))` |
| D | % Part. | `=SI($B77="";"";SI.ERROR($C77/$C$87;0))` |
| E | Valor impactado | `=SI($B77="";"";SUMAR.SI.CONJUNTO(NOVEDADES!$R$4:$R$2003;NOVEDADES!$T$4:$T$2003;$B77;$P))` |

### 7.7 Consulta rápida de pedido (`N12:O23`)

Se digita el pedido en `O13` (amarilla) y devuelve la ficha completa.

| Celda | Campo | Fórmula |
|---|---|---|
| `O14` | Cliente | `=SI($O$13="";"—";SI.ERROR(INDICE(DESPACHOS!$D$3:$D$3002;COINCIDIR($O$13;DESPACHOS!$B$3:$B$3002;0));"NO EXISTE"))` |
| `O15` | # Factura | igual, con `DESPACHOS!$C$3:$C$3002` |
| `O16` | Destino / Ciudad | igual, con `DESPACHOS!$K$3:$K$3002` |
| `O17` | Transportadora | igual, con `DESPACHOS!$F$3:$F$3002` |
| `O18` | Placa | igual, con `DESPACHOS!$H$3:$H$3002` |
| `O19` | Fecha despacho | igual, con `DESPACHOS!$J$3:$J$3002` |
| `O20` | Novedades del pedido | `=SI($O$13="";"—";CONTAR.SI.CONJUNTO(NOVEDADES!$C$4:$C$2003;$O$13))` |
| `O21` | Valor afectado | `=SI($O$13="";"—";SUMAR.SI.CONJUNTO(NOVEDADES!$R$4:$R$2003;NOVEDADES!$C$4:$C$2003;$O$13))` |
| `O22` | Estado más reciente | `=SI($O$13="";"—";SI.ERROR(BUSCAR(2;1/(NOVEDADES!$C$4:$C$2003=$O$13);NOVEDADES!$T$4:$T$2003);"—"))` |
| `O23` | Semáforo SLA | `=SI($O$13="";"—";SI.ERROR(BUSCAR(2;1/(NOVEDADES!$C$4:$C$2003=$O$13);NOVEDADES!$Y$4:$Y$2003);"—"))` |

`BUSCAR(2;1/(rango=valor);resultado)` devuelve la **última** coincidencia, no la primera: es lo
correcto cuando un pedido acumula varias novedades y se quiere ver el estado vigente.

---

## 8. Verificación

Las fórmulas se evaluaron con un motor de cálculo independiente (`formulas`) sobre un libro
sembrado con datos reales de GESTOAGRO: **1.186 celdas calculadas, 0 errores**
(`#N/A`, `#REF!`, `#VALUE!`, `#DIV/0!`, `#NAME?`, `#NUM!`, `#NULL!`).

Casos verificados: cruce correcto por llave; `SIN DESPACHO` para pedidos inexistentes;
`DUPLICADO` detectado; semáforo devolviendo los cinco estados; ratio de incidencia, top causas,
tabla por transportadora y consulta rápida con pedido vacío.

---

## 9. Notas de portabilidad

| Tema | Excel 365 / 2021 | Excel 2010-2019 | Google Sheets |
|---|---|---|---|
| `ÍNDICE`+`COINCIDIR` | ✅ | ✅ | ✅ |
| `BUSCARX` | ✅ | ❌ | ❌ |
| `DIA.LAB` | ✅ | ✅ | ✅ |
| Nombres con `DESREF` | ✅ | ✅ | ❌ — apunte la validación al rango directo `LISTAS!A3:A42` |
| Formato condicional con referencia a otra hoja | ✅ | ✅ (2010+) | ✅ |
| Comodín `"CERRADA*"` en `CONTAR.SI.CONJUNTO` | ✅ | ✅ | ✅ |

---

## 10. Operación y cierre

1. **DESPACHOS**: pegar el export de Access desde la fila 3 (columnas A a J). Completar `K`, `L`, `M`.
2. **NOVEDADES**: digitar `B` (fecha) y `C` (pedido). Elegir `L`, `M`, `O`, `T` de las listas. Registrar `Q` y `R`.
3. Al resolver: cambiar `T` a un estado que cierre y escribir `V`.
4. **DASHBOARD**: ajustar el periodo y leer.
5. **Cierre mensual**: guardar copia con el nombre del mes en `Históricos/`, borrar solo las celdas amarillas del archivo activo.
