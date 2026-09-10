# Matriz de Novedades · Logística y Transporte

Un solo archivo Excel para registrar todo lo que sale mal —en la carretera y dentro de la
empresa—, saber a quién cobrárselo y medir si la operación está mejorando.

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
| **Un solo registro de incidentes** | Novedades en ruta e internas en la misma matriz, separadas por una columna `Origen`, como en cualquier registro de incidentes serio |
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

**Llave de cruce:** el `Nº Guía / Remisión`. Se digita en `NOVEDADES!D` y trae todo desde `ENVIOS`.

### Las dos clases de novedad

| | `En ruta` | `Interna` |
|---|---|---|
| Qué es | Pasó con un envío ya despachado | Pasó dentro de la empresa, casi siempre antes de despachar |
| Ejemplos | Cliente ausente, avería, rechazo, retraso | Error de alistamiento, descuadre de inventario, demora en el cargue, falla de un montacargas, accidente laboral |
| ¿Lleva guía? | Sí | No — se deja vacía |
| ¿Entra al scorecard de transportadoras? | Sí | **No** |
| ¿Entra a la tasa de novedades por envío? | Sí | **No** |
| ¿Entra al Pareto, las 6M y el punto de ocurrencia? | Sí | Sí |

La exclusión es automática, no una regla aparte: las internas dejan la guía y la transportadora
en blanco, así que ningún `CONTAR.SI.CONJUNTO` por transportadora o por envío las alcanza.

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
| N | Novedades | ⬜ | `=SI($A4="";"";CONTAR.SI.CONJUNTO(NOVEDADES!$D$4:$D$1503;$A4))` |
| O | ¿Llegó completa? | ⬜ | `=SI($A4="";"";SI(CONTAR.SI.CONJUNTO(NOVEDADES!$D$4:$D$1503;$A4;NOVEDADES!$N$4:$N$1503;"SÍ")>0;"No";"Sí"))` |
| P | OTIF | ⬜ | `=SI(O($A4="";$K4="");"";SI(Y($M4="Sí";$O4="Sí");"OTIF";"Falló"))` |

> `Fecha promesa de entrega` es la columna que hace posible medir OTIF. Sin ella no hay indicador.

---

## Hoja `NOVEDADES`

28 columnas en cinco bloques. **Solo 13 se digitan.**

### ① Identificar

| Col | Encabezado | Tipo | Fórmula |
|---|---|---|---|
| A | ID | ⬜ | `=SI($B4="";"";"N-"&TEXTO(FILA()-3;"0000"))` |
| B | Fecha de la novedad | 🟨 | — |
| **C** | **Origen** | 🟨 lista | `En ruta` / `Interna` |
| D | Nº Guía / Remisión | 🟨 (solo si es en ruta) | — |
| E | Validación | ⬜ | ver abajo |
| F | Cliente | ⬜ | `=SI($D4="";"";SI.ERROR(INDICE(ENVIOS!$C$4:$C$3003;COINCIDIR($D4;ENVIOS!$A$4:$A$3003;0));"—"))` |
| G | Ciudad destino | ⬜ | igual, con `ENVIOS!$D$4:$D$3003` |
| H | Transportadora | ⬜ | igual, con `ENVIOS!$E$4:$E$3003` |
| I | Conductor | ⬜ | igual, con `ENVIOS!$F$4:$F$3003` |
| J | Placa | ⬜ | igual, con `ENVIOS!$G$4:$G$3003` |
| K | Fecha despacho | ⬜ | igual, con `ENVIOS!$B$4:$B$3003` |

**E — Validación**, que ya no castiga a una novedad interna por no tener guía:

```excel
=SI($C4="";"";SI($D4="";SI($C4="Interna";"Sin guía (interna)";"FALTA GUÍA");
  SI(CONTAR.SI.CONJUNTO(ENVIOS!$A$4:$A$3003;$D4)=0;"NO EXISTE";
  SI(CONTAR.SI.CONJUNTO(ENVIOS!$A$4:$A$3003;$D4)>1;"DUPLICADA";"OK"))))
```

| Valor | Cuándo | Color |
|---|---|---|
| `OK` | La guía existe una sola vez | verde |
| `Sin guía (interna)` | Origen interno y sin guía: correcto | gris |
| `FALTA GUÍA` | Origen «En ruta» pero no escribió la guía | rojo |
| `NO EXISTE` | La guía no está en `ENVIOS` | rojo |
| `DUPLICADA` | La guía aparece más de una vez | ámbar |

### ② Clasificar

| Col | Encabezado | Tipo | Fórmula |
|---|---|---|---|
| L | Tipo de novedad | 🟨 lista | — |
| M | Gravedad | ⬜ | `=SI($L4="";"";SI.ERROR(INDICE(CONFIG!$C$4:$C$63;COINCIDIR($L4;CONFIG!$A$4:$A$63;0));"Media"))` |
| N | ¿Afecta la entrega? | ⬜ | `=SI($L4="";"";SI($C4="Interna";"NO";SI.ERROR(INDICE(CONFIG!$E$4:$E$63;COINCIDIR($L4;CONFIG!$A$4:$A$63;0));"NO")))` |
| **O** | **Punto de ocurrencia** | 🟨 lista | — |
| P | Causa raíz | 🟨 lista | — |
| Q | Familia (6M) | ⬜ | `=SI($P4="";"";SI.ERROR(INDICE(CONFIG!$H$4:$H$63;COINCIDIR($P4;CONFIG!$G$4:$G$63;0));"Por definir"))` |
| R | Área responsable | ⬜ | `=SI($P4="";"";SI.ERROR(INDICE(CONFIG!$I$4:$I$63;COINCIDIR($P4;CONFIG!$G$4:$G$63;0));"Por definir"))` |

`¿Afecta la entrega?` alimenta el «in full» de OTIF. Una novedad interna nunca afecta una
entrega, porque no hay entrega: por eso la fórmula la fuerza a `NO`.

**`Origen` y `Punto de ocurrencia` no son lo mismo, y ahí está el valor:**

- `Origen` responde *¿esto pertenece a un envío despachado?* Decide si lleva guía y si entra al
  scorecard del transportador.
- `Punto de ocurrencia` responde *¿dónde se rompió?* Un faltante detectado en ruta puede tener
  punto de ocurrencia «Alistamiento (picking)»: se descubrió afuera, pero nació adentro.

### ③ Impacto

| Col | Encabezado | Tipo |
|---|---|---|
| S | Unidades afectadas | 🟨 |
| T | Valor afectado | 🟨 |

### ④ Gestionar y cerrar

| Col | Encabezado | Tipo | Fórmula |
|---|---|---|---|
| U | Estado | 🟨 lista | — |
| V | Responsable | 🟨 lista | — |
| W | Fecha límite | ⬜ | `=SI(O($B4="";$L4="");"";DIA.LAB($B4;SI.ERROR(INDICE(CONFIG!$D$4:$D$63;COINCIDIR($L4;CONFIG!$A$4:$A$63;0));3)))` |
| X | Fecha de solución | 🟨 | — |
| Y | Días abiertos | ⬜ | `=SI($B4="";"";SI($X4<>"";$X4-$B4;HOY()-$B4))` |
| Z | Estado SLA | ⬜ | ver abajo |

```excel
=SI($B4="";"";SI(SI.ERROR(INDICE(CONFIG!$L$4:$L$63;COINCIDIR($U4;CONFIG!$K$4:$K$63;0));"NO")="SÍ";
  SI(O($X4="";$W4="");"Resuelta";SI($X4>$W4;"Resuelta tarde";"Resuelta a tiempo"));
  SI($W4="";"Sin clasificar";SI(HOY()>$W4;"Vencida";SI(HOY()>=$W4-1;"Por vencer";"En plazo")))))
```

No tiene ningún estado escrito a mano: lee la columna `¿CIERRA EL CASO?` de `CONFIG`. Y ya no
depende de la guía, sino de la fecha, para que las novedades internas también tengan semáforo.

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
| AA | Qué se hizo | 🟨 |
| AB | Notas / soporte | 🟨 |

---

## Hoja `CONFIG`

Todo el comportamiento del archivo se cambia aquí, sin tocar fórmulas.

| Rango | Contenido | Alimenta |
|---|---|---|
| `A4:E63` | Tipo · Ámbito · Gravedad · SLA (días hábiles) · ¿Afecta la entrega? | `NOVEDADES!L,M,N,W` |
| `G4:I63` | Causa raíz · Familia 6M · Área responsable | `NOVEDADES!P,Q,R` |
| `K4:L63` | Estado · ¿Cierra el caso? | `NOVEDADES!U,Z` |
| `N4:N63` | Punto de ocurrencia | `NOVEDADES!O` |
| `P4:P63` | Origen (`En ruta` / `Interna`) | `NOVEDADES!C` |
| `R4:R63` | Transportadora | `ENVIOS!E` + scorecard |
| `T4:T63` | Responsable | `NOVEDADES!V` |
| `V4:V33` | Auxiliar del Pareto — no borrar | `TABLERO` |

El **primer** punto de la lista `N` debe ser «En ruta / entrega al cliente»: el KPI «punto interno
más frecuente» lo excluye a propósito, mirando de `N5` hacia abajo.

### Tipos de novedad

31 tipos: 19 de ruta y 12 internos.

| Tipo | Ámbito | Gravedad | SLA | ¿Afecta? |
|---|---|---|---|---|
| Vehículo varado / falla mecánica | En ruta | Crítica | 1 | SÍ |
| Pérdida o robo de mercancía | En ruta | Crítica | 1 | SÍ |
| Retraso en vía | En ruta | Alta | 1 | NO |
| Cliente rechaza el envío | En ruta | Alta | 2 | SÍ |
| Faltante (llegó de menos) | En ruta | Alta | 2 | SÍ |
| Producto equivocado | En ruta | Alta | 2 | SÍ |
| Pago contraentrega fallido | En ruta | Alta | 2 | SÍ |
| Avería / producto dañado | En ruta | Alta | 3 | SÍ |
| Producto vencido o próximo a vencer | En ruta | Alta | 3 | SÍ |
| Cliente ausente / no atiende | En ruta | Media | 2 | SÍ |
| Dirección errada o incompleta | En ruta | Media | 2 | SÍ |
| Cliente cerrado / fuera de horario | En ruta | Media | 2 | SÍ |
| Zona restringida o sin acceso | En ruta | Media | 3 | SÍ |
| Empaque en mal estado | En ruta | Media | 3 | NO |
| Soporte de entrega sin firmar | En ruta | Media | 4 | NO |
| Error en factura o precio | En ruta | Media | 5 | NO |
| Entrega parcial acordada | En ruta | Baja | 5 | SÍ |
| Sobrante (llegó de más) | En ruta | Baja | 5 | NO |
| Flete no liquidado | En ruta | Baja | 5 | NO |
| Incidente de seguridad o accidente laboral | Interna | Crítica | 1 | NO |
| Diferencia de inventario | Interna | Alta | 3 | NO |
| Producto averiado en bodega | Interna | Alta | 2 | NO |
| Producto vencido en bodega | Interna | Alta | 3 | NO |
| Derrame o daño en manipulación interna | Interna | Alta | 2 | NO |
| Falla de equipo en bodega | Interna | Alta | 1 | NO |
| Error de alistamiento detectado en bodega | Interna | Media | 1 | NO |
| Demora en el cargue | Interna | Media | 1 | NO |
| Demora en facturación o documentos | Interna | Media | 2 | NO |
| Pedido mal digitado (antes del despacho) | Interna | Media | 1 | NO |
| Devolución recibida sin soporte | Interna | Media | 3 | NO |
| Faltante de personal en el turno | Interna | Media | 1 | NO |

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
| Falta de espacio u orden en bodega | Método | Bodega |
| Personal insuficiente en el turno | Mano de obra | Bodega |
| Equipo de bodega fuera de servicio | Máquina | Bodega |
| Procedimiento no seguido | Método | Operaciones |
| Documentación incompleta | Método | Facturación |
| Sin clasificar aún | Por definir | Por definir |

### Puntos de ocurrencia

En ruta / entrega al cliente · Recepción de proveedor · Almacenamiento · Alistamiento (picking) ·
Empaque · Cargue del vehículo · Despacho y coordinación · Facturación y documentos ·
Bodega de devoluciones · Patio / zona de maniobras · Oficina / administrativo · Otro

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
| `TIPOS_NOVEDAD` | `=DESREF(CONFIG!$A$4;0;0;MAX(1;CONTARA(CONFIG!$A$4:$A$63));1)` |
| `CAUSAS_RAIZ` | `=DESREF(CONFIG!$G$4;0;0;MAX(1;CONTARA(CONFIG!$G$4:$G$63));1)` |
| `ESTADOS_NOVEDAD` | `=DESREF(CONFIG!$K$4;0;0;MAX(1;CONTARA(CONFIG!$K$4:$K$63));1)` |
| `PUNTOS_OCURRENCIA` | `=DESREF(CONFIG!$N$4;0;0;MAX(1;CONTARA(CONFIG!$N$4:$N$63));1)` |
| `ORIGENES` | `=DESREF(CONFIG!$P$4;0;0;MAX(1;CONTARA(CONFIG!$P$4:$P$63));1)` |
| `TRANSPORTADORAS` | `=DESREF(CONFIG!$R$4;0;0;MAX(1;CONTARA(CONFIG!$R$4:$R$63));1)` |
| `RESPONSABLES` | `=DESREF(CONFIG!$T$4;0;0;MAX(1;CONTARA(CONFIG!$T$4:$T$63));1)` |

| Rango | Regla | Estilo |
|---|---|---|
| `NOVEDADES!C` | Lista de orígenes | 🛑 Bloquea |
| `NOVEDADES!L` · `O` · `P` · `U` · `V` | Listas | 🛑 Bloquea |
| `NOVEDADES!B` | Fecha entre 2020 y 2040 | 🛑 Bloquea |
| `NOVEDADES!X` | `=O($X4="";Y(ESNUMERO($X4);$X4>=$B4))` | 🛑 Bloquea |
| `NOVEDADES!S` · `T` | Número ≥ 0 | 🛑 Bloquea |
| `ENVIOS!E` | Lista de transportadoras | ⚠️ Advierte |
| `ENVIOS!B` · `J` · `K` | Fecha válida | ⚠️ Advierte |
| `ENVIOS!H` · `I` | Número ≥ 0 | ⚠️ Advierte |

En `ENVIOS` la validación advierte pero no bloquea, para no interrumpir un pegado masivo.
El Nº de guía de `NOVEDADES` **no** lleva validación a propósito: debe poder quedar vacío
cuando la novedad es interna.

## Formato condicional

| Hoja | Rango | Regla | Color |
|---|---|---|---|
| NOVEDADES | `Z` Estado SLA | En plazo / Por vencer / Vencida | verde / ámbar / rojo |
| NOVEDADES | `Z` | Resuelta a tiempo / tarde / sin fecha | azul / naranja / gris |
| NOVEDADES | `M` Gravedad | Crítica / Alta / Media / Baja | rojo sólido / rojo / ámbar / verde |
| NOVEDADES | `C` Origen | `Interna` / `En ruta` | azul / gris |
| NOVEDADES | `N` ¿Afecta la entrega? | `SÍ` | ámbar |
| NOVEDADES | `E` Validación | OK · Sin guía (interna) · FALTA GUÍA · NO EXISTE · DUPLICADA | verde · gris · rojo · rojo · ámbar |
| NOVEDADES | `U` Estado | `Sin gestionar` → rojo; cierra=SÍ → verde; resto → ámbar (leído de `CONFIG`) | |
| NOVEDADES | `X` | `=Y($X4="";$Z4="Resuelta")` — cerró sin fecha | rojo |
| NOVEDADES | `T`, `Y` | Barra de datos | ámbar / gris |
| NOVEDADES | `A:AB` | `=$Z4="Vencida"` → texto rojo en toda la fila | |
| ENVIOS | `M`, `O`, `P` | Sí / No / OTIF / Falló / En ruta / Atrasado | verde / rojo / gris |
| ENVIOS | `N` | `> 0` | ámbar |
| ENVIOS | `A:P` | Guía duplicada en la base | texto naranja |
| TABLERO | KPIs | OTIF ≥95% verde · <90% rojo · tasa >5% rojo · vencidas >0 rojo · SLA <90% rojo · % internas >30% ámbar | |
| TABLERO | `M18:M27` | Nota A / B / C / D | verde / azul / ámbar / rojo |
| TABLERO | `G49:G80` | Ámbito `Interna` / `En ruta` | azul / gris |
| TABLERO | `F33:F44` | `% acumulado ≤ 80%` → resaltado: son las causas a atacar | ámbar |

El resaltado de fila vencida usa solo tipografía, no relleno, para no tapar el código de colores.

---

## Hoja `TABLERO`

Periodo en `E4` (Desde) y `G4` (Hasta). Abajo, `$PN` y `$PE` abrevian los criterios de periodo:

- `$PN` = `NOVEDADES!$B$4:$B$1503;">="&$E$4;NOVEDADES!$B$4:$B$1503;"<="&$G$4`
- `$PE` = `ENVIOS!$B$4:$B$3003;">="&$E$4;ENVIOS!$B$4:$B$3003;"<="&$G$4`
- `$ENTREGADOS` = `(CONTAR.SI.CONJUNTO(ENVIOS!$P$4:$P$3003;"OTIF";$PE)+CONTAR.SI.CONJUNTO(ENVIOS!$P$4:$P$3003;"Falló";$PE))`

### KPIs

**Fila 1 — LAS ENTREGAS** (solo mira envíos, así que las novedades internas no la tocan)

| Celda | KPI | Fórmula |
|---|---|---|
| `D7` | **OTIF** | `=SI.ERROR(CONTAR.SI.CONJUNTO(ENVIOS!$P$4:$P$3003;"OTIF";$PE)/$ENTREGADOS;"—")` |
| `F7` | Entregas a tiempo | `=SI.ERROR(CONTAR.SI.CONJUNTO(ENVIOS!$M$4:$M$3003;"Sí";$PE)/$ENTREGADOS;"—")` |
| `H7` | **Tasa de novedades** | `=SI.ERROR(CONTAR.SI.CONJUNTO(ENVIOS!$N$4:$N$3003;">0";$PE)/CONTAR.SI.CONJUNTO($PE);"—")` |
| `J7` | Valor afectado | `=SUMAR.SI.CONJUNTO(NOVEDADES!$T$4:$T$1503;$PN)` |
| `L7` | Envíos del periodo | `=CONTAR.SI.CONJUNTO($PE)` |

**Fila 2 — LA GESTIÓN** (todas las novedades, en ruta e internas)

| Celda | KPI | Fórmula |
|---|---|---|
| `D10` | Novedades | `=CONTAR.SI.CONJUNTO($PN)` |
| `F10` | Abiertas | `=CONTAR.SI.CONJUNTO(NOVEDADES!$Z$4:$Z$1503;"En plazo";$PN)+…"Por vencer"…+…"Vencida"…+…"Sin clasificar"…` |
| `H10` | Vencidas | `=CONTAR.SI.CONJUNTO(NOVEDADES!$Z$4:$Z$1503;"Vencida";$PN)` |
| `J10` | Días prom. de solución | `=SI.ERROR(REDONDEAR(PROMEDIO.SI.CONJUNTO(NOVEDADES!$Y$4:$Y$1503;$PN);1);0)` |
| `L10` | **Cumplimiento de SLA** | `=SI.ERROR(CONTAR.SI.CONJUNTO(NOVEDADES!$Z$4:$Z$1503;"Resuelta a tiempo";$PN)/CONTAR.SI.CONJUNTO(NOVEDADES!$Z$4:$Z$1503;"Resuelta*";$PN);"—")` |

**Fila 3 — DÓNDE NACEN**

| Celda | KPI | Fórmula |
|---|---|---|
| `D13` | En ruta (transporte) | `=CONTAR.SI.CONJUNTO(NOVEDADES!$C$4:$C$1503;"En ruta";$PN)` |
| `F13` | Internas (la empresa) | `=CONTAR.SI.CONJUNTO(NOVEDADES!$C$4:$C$1503;"Interna";$PN)` |
| `H13` | **% internas** | `=SI.ERROR(CONTAR.SI.CONJUNTO(NOVEDADES!$C$4:$C$1503;"Interna";$PN)/CONTAR.SI.CONJUNTO($PN);"—")` |
| `J13` | Valor de las internas | `=SUMAR.SI.CONJUNTO(NOVEDADES!$T$4:$T$1503;NOVEDADES!$C$4:$C$1503;"Interna";$PN)` |
| `L13` | Punto interno más frecuente | `=SI(MAX($D$87:$D$97)=0;"—";SI.ERROR(INDICE($B$87:$B$97;COINCIDIR(MAX($D$87:$D$97);$D$87:$D$97;0));"—"))` |

`L13` arranca en la fila 87 y no en la 86 a propósito: se salta «En ruta / entrega al cliente»
para señalar un punto de la casa propia, que es lo accionable.

**Por qué la tasa de novedades cuenta envíos y no novedades:** un envío puede generar tres
incidencias. Dividir novedades entre envíos daría un porcentaje inflado que puede pasar del 100%.
`ENVIOS!N` marca el envío una sola vez, así que responde la pregunta correcta: *de cada 100
envíos, ¿cuántos salieron mal?*

**Por qué el denominador de OTIF se cuenta como `OTIF + Falló`:** solo se puede evaluar un envío
ya entregado. Contarlo de forma explícita es más robusto que usar el criterio `"<>"` sobre la
fecha de entrega.

### Scorecard de transportadoras (filas 18-27)

Solo cuenta novedades **en ruta**: las internas no son culpa del transportador. La exclusión sale
sola porque las internas dejan `NOVEDADES!H` (transportadora) vacía.

| Col | Métrica | Fórmula (fila 18; `$e` = `ENVIOS!$E$4:$E$3003;$B18`, `$g` = `NOVEDADES!$H$4:$H$1503;$B18`) |
|---|---|---|
| B | Transportadora | `=SI(CONFIG!$R4="";"";CONFIG!$R4)` |
| D | Envíos | `=SI($B18="";"";CONTAR.SI.CONJUNTO($e;$PE))` |
| E | OTIF | `=SI($B18="";"";SI.ERROR(CONTAR.SI.CONJUNTO($e;ENVIOS!$P$4:$P$3003;"OTIF";$PE)/(CONTAR.SI.CONJUNTO($e;ENVIOS!$P$4:$P$3003;"OTIF";$PE)+CONTAR.SI.CONJUNTO($e;ENVIOS!$P$4:$P$3003;"Falló";$PE));"—"))` |
| F | Novedades | `=SI($B18="";"";CONTAR.SI.CONJUNTO($g;$PN))` |
| G | Tasa | `=SI($B18="";"";SI.ERROR(CONTAR.SI.CONJUNTO($e;ENVIOS!$N$4:$N$3003;">0";$PE)/$D18;"—"))` |
| H | Abiertas | suma de 4 `CONTAR.SI.CONJUNTO` sobre `NOVEDADES!$Z` |
| I | Vencidas | `=SI($B18="";"";CONTAR.SI.CONJUNTO($g;NOVEDADES!$Z$4:$Z$1503;"Vencida";$PN))` |
| J | Días prom. | `=SI($B18="";"";SI.ERROR(REDONDEAR(PROMEDIO.SI.CONJUNTO(NOVEDADES!$Y$4:$Y$1503;$g;$PN);1);0))` |
| K | Valor afectado | `=SI($B18="";"";SUMAR.SI.CONJUNTO(NOVEDADES!$T$4:$T$1503;$g;$PN))` |
| L | **Puntaje** | `=SI(O($B18="";$D18=0;NO(ESNUMERO($E18)));"—";REDONDEAR($E18*60+(1-N($G18))*25+SI($F18=0;15;(1-$I18/$F18)*15);0))` |
| M | **Nota** | `=SI(NO(ESNUMERO($L18));"—";SI($L18>=90;"A";SI($L18>=80;"B";SI($L18>=70;"C";"D"))))` |

**Puntaje** = OTIF ×60 + (1 − tasa de novedades) ×25 + (1 − vencidas/novedades) ×15.
**Nota:** A ≥ 90 · B 80-89 · C 70-79 · D < 70.

### Pareto de causa raíz (filas 33-44)

Auxiliar en `CONFIG!V4:V33`:
`=SI($G4="";"";CONTAR.SI.CONJUNTO(NOVEDADES!$P$4:$P$1503;$G4;NOVEDADES!$B$4:$B$1503;">="&TABLERO!$E$4;NOVEDADES!$B$4:$B$1503;"<="&TABLERO!$G$4)+FILA()/100000)`

El `+FILA()/100000` es un desempate infinitesimal: sin él, dos causas con el mismo número de
casos harían que `COINCIDIR` devolviera siempre la misma y el ranking repetiría filas.

| Col | Fórmula (fila 33, puesto 1) |
|---|---|
| B | `=SI.ERROR(INDICE(CONFIG!$G$4:$G$33;COINCIDIR(K.ESIMO.MAYOR(CONFIG!$V$4:$V$33;1);CONFIG!$V$4:$V$33;0));"")` |
| D | `=SI($B33="";"";REDONDEAR.MENOS(K.ESIMO.MAYOR(CONFIG!$V$4:$V$33;1);0))` |
| E | `=SI($B33="";"";SI.ERROR($D33/$D$45;0))` |
| F | `=SI($B33="";"";SI.ERROR(SUMA($D$33:$D33)/$D$45;0))` |
| G | `=SI($B33="";"";SUMAR.SI.CONJUNTO(NOVEDADES!$T$4:$T$1503;NOVEDADES!$P$4:$P$1503;$B33;$PN))` |

En las filas 34 a 44 cambie el `1` de `K.ESIMO.MAYOR` por 2, 3, … 12.

### Punto de ocurrencia (filas 86-97)

La tabla que responde *¿en qué parte de la operación se rompe?* Mezcla en ruta e internas a
propósito: un faltante detectado en la entrega pero originado en picking aparece en
«Alistamiento», que es donde hay que arreglarlo.

| Col | Fórmula (fila 86; `$q` = `NOVEDADES!$O$4:$O$1503;$B86`) |
|---|---|
| B | `=SI(CONFIG!$N4="";"";CONFIG!$N4)` |
| D | `=SI($B86="";"";CONTAR.SI.CONJUNTO($q;$PN))` |
| E | `=SI($B86="";"";SI.ERROR($D86/$D$98;0))` |
| F | `=SI($B86="";"";SUMAR.SI.CONJUNTO(NOVEDADES!$T$4:$T$1503;$q;$PN))` |
| G | Abiertas — suma de 4 `CONTAR.SI.CONJUNTO` sobre `NOVEDADES!$Z` |
| H | `=SI($B86="";"";CONTAR.SI.CONJUNTO($q;NOVEDADES!$Z$4:$Z$1503;"Vencida";$PN))` |
| I | `=SI($B86="";"";SI.ERROR(REDONDEAR(PROMEDIO.SI.CONJUNTO(NOVEDADES!$Y$4:$Y$1503;$q;$PN);1);0))` |

### Gráficas

Cinco gráficas nativas de Excel a la derecha de las tablas (columnas O a V). Se recalculan
solas con el periodo, porque leen las mismas celdas de las tablas.

| Gráfica | Lee | Ancla |
|---|---|---|
| OTIF por transportadora (columnas) | `B18:B27` × `E18:E27` | `O17` |
| Causas que más pesan (barras) | `B33:B44` × `D33:D44` | `O35` |
| Novedades por tipo (barras) | `B49:B80` × `D49:D80` | `O59` |
| Dónde se rompe la operación (barras) | `B86:B97` × `D86:D97` | `O95` |
| Estado de la gestión (barras) | `B102:B107` × `D102:D107` | `O119` |

### Otras secciones

- **Novedades por tipo** (filas 49-80): casos, %, valor, ámbito, gravedad, abiertas, vencidas, días prom.
- **Estado de la gestión** y **Familia 6M** (filas 102-110), lado a lado.
- **Buscador** (fila 113): se escribe la guía en `D113` y sale la ficha completa. Solo aplica a
  novedades en ruta. Las últimas novedades usan
  `=BUSCAR(2;1/(NOVEDADES!$D$4:$D$1503=$D$113);NOVEDADES!$Z$4:$Z$1503)`, que devuelve la
  **última** coincidencia y no la primera.

---

## Verificación

Las fórmulas se evaluaron con un motor de cálculo independiente (`formulas`) sobre un libro
sembrado con 30 envíos y 22 novedades —14 en ruta y 8 internas—: **2.515 celdas calculadas,
0 errores** (`#N/A`, `#REF!`, `#VALUE!`, `#DIV/0!`, `#NAME?`, `#NUM!`, `#NULL!`).

Resultados del ejemplo, contrastados a mano:

| | |
|---|---|
| OTIF | 67,9% (19 de 28 entregados) |
| Entregas a tiempo | 71,4% |
| Tasa de novedades | 40,0% (12 de 30 envíos) |
| Cumplimiento de SLA | 90,9% |
| En ruta / internas | 14 / 8 — **36,4% internas** |
| Punto interno más frecuente | Alistamiento (picking) |
| Scorecard | de 97 puntos (nota A) a 38 (nota D) |

**La prueba clave del aislamiento:** al pasar de 14 a 22 novedades sumando 8 internas, el
scorecard no se movió ni un punto (A=97, B=61, C=38, Flota propia=65), y OTIF, entregas a tiempo
y tasa de novedades quedaron idénticos. Las internas no contaminan la evaluación del
transportador.

También verificados: la validación devolviendo `Sin guía (interna)` en vez de un error para las
8 internas, el ID y el semáforo SLA funcionando sin guía, los siete valores del semáforo, el
Pareto con su acumulado, el buscador con el campo vacío y los anclajes de las cinco gráficas
(ninguna se monta sobre otra).

El ejemplo incluye a propósito un envío que llegó puntual pero incompleto (`G-2426`), para que se
vea por qué «entregas a tiempo» (71,4%) es mayor que OTIF (67,9%): llegar a tiempo no basta.

Defectos encontrados y corregidos durante estas verificaciones:

1. El denominador de OTIF contaba las entregas hechas con `CONTAR.SI.CONJUNTO(rango;"<>")`; el
   conteo salía mal y el OTIF daba 150%. Se reemplazó por la suma explícita de `OTIF` + `Falló`.
2. El mismo error en el OTIF por transportadora del scorecard.
3. El total del Pareto usaba el mismo criterio y daba 0, dejando todos los porcentajes en cero.
4. Los anclajes iniciales de las gráficas se solapaban entre sí.
5. Al abrir la matriz a las novedades internas, el `ID` y el `Estado SLA` colgaban del Nº de
   guía, así que una novedad sin guía se quedaba sin identificador y sin semáforo. Ambos pasaron
   a colgar de la fecha.
6. El KPI «punto más frecuente» devolvía «En ruta / entrega al cliente», que no dice nada
   accionable. Ahora excluye ese punto y señala uno de la casa propia.

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
- Para una novedad interna: marque `Origen` = `Interna` y **deje el Nº de guía vacío**. La
  validación dirá «Sin guía (interna)», que es lo correcto.
- Antes de empezar, reemplace «Transportadora A, B, C» en `CONFIG!M` por los nombres reales.
