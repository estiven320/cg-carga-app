# Informe Power BI · GESTOAGRO

Proyecto de Power BI generado a partir de `GESTOAGRO_PowerBI_datos.xlsx`.

Está en formato **PBIP** (Power BI Project): carpetas de texto plano en vez de un
`.pbix` binario, así que se puede versionar y revisar en git como cualquier código.

```
powerbi/
├── GESTOAGRO/
│   ├── GESTOAGRO.pbip              ← abre este archivo con Power BI Desktop
│   ├── GESTOAGRO.SemanticModel/    ← modelo: tablas, relaciones, medidas (TMDL)
│   └── GESTOAGRO.Report/           ← informe: 6 páginas, 70 visuales (PBIR)
├── datos/
│   └── GESTOAGRO_PowerBI_datos.xlsx
└── tools/                          ← scripts que generan y verifican el proyecto
```

## Cómo abrirlo

1. Abre `powerbi/GESTOAGRO/GESTOAGRO.pbip` con **Power BI Desktop**.
2. Si el Excel no está en la ruta esperada, ajusta el parámetro **RutaArchivo**
   en *Inicio → Transformar datos → Administrar parámetros*.
   Valor por defecto: `C:\Users\braya\OneDrive\Escritorio\power bi\GESTOAGRO_PowerBI_datos.xlsx`
3. **Actualizar**.

> **Requisito**: el formato PBIR del informe necesita Power BI Desktop de 2024 o
> posterior. Si tu versión lo pide, actívalo en
> *Archivo → Opciones → Características de vista previa → Power BI Project (.pbip)*.

## El modelo

Esquema en estrella con una sola tabla de hechos para las guías:

```
                 Dim_Calendario
                        │
   Dim_Clientes ──── Fact_Guias ──── Dim_Transportadora
        │                │
        │            Dim_Ruta
        │
  Fact_Devoluciones ──── Dim_Productos
```

**`Fact_Guias` (183 filas)** fusiona las dos hojas de hechos del Excel. La clave
compuesta `# Planilla + # Pedido + # Factura` es única en ambas y cruza 183 de 183,
así que `Fact_Despachos` (peso, vehículo, conductor) y `Fact_Cumplidos` (plazo,
fecha límite, semáforo) describen las mismas guías y se unen en una sola tabla.
`# Factura` por sí sola **no** sirve como clave: se repite 18 veces en cada hoja.

Otras decisiones de modelado:

| Situación en los datos | Qué hace el modelo |
|---|---|
| `Nombre SN` tiene 9 nombres repetidos con códigos distintos (errores de digitación) | `Dim_Clientes` se deduplica por nombre normalizado: 1.545 → 1.536 filas, para que la relación sea 1 a varios |
| 62 guías sin `RUTA` en despachos | Se toma la `Ruta` de cumplidos, que las tiene todas; queda 0 sin ruta |
| 32 guías sin `Ciudad` | Se intenta recuperar del maestro de clientes; hoy no recupera ninguna (esos clientes también la tienen vacía), quedan como `SIN CIUDAD`. La columna `Origen Ciudad` deja ver de dónde salió cada una |
| `Fact_Devoluciones` está vacía | La tabla se crea igual con toda su estructura y sus relaciones, lista para cuando se empiece a diligenciar |
| `Dim_Productos` no tiene hechos que la enlacen | Se incluye como catálogo, relacionada solo con devoluciones (el único sitio donde hay detalle por producto) |

## Las páginas

| # | Página | Para qué |
|---|---|---|
| 1 | **Resumen ejecutivo** | Volumen del período: guías, kilos, planillas, clientes, reparto por transportadora y por ruta |
| 2 | **Cumplimiento** | Estado de entrega, mora por ruta y por transportadora, detalle guía a guía |
| 3 | **Transporte** | Flota propia vs. terceros, conductores, vehículos, productividad por planilla |
| 4 | **Clientes y destinos** | Concentración de kilos por cliente y por ciudad |
| 5 | **Devoluciones** | Lista para usar; hoy sin datos |
| 6 | **Calidad de datos** | Los vacíos que hay que corregir en el Excel |

## Advertencia importante sobre el cumplimiento

**Las columnas `Estado cumplido`, `Fecha recibido` y `Responsable` están vacías en
las 183 guías.** Sin fecha de recibido no hay forma de saber si algo se entregó, así
que el informe expone dos lecturas distintas y no las mezcla:

- **`Semáforo Origen`** — la columna `Semáforo` del Excel tal cual. Reparte las guías
  en *Por vencer* (121), *VENCIDO* (31) y *En plazo* (31), pero está **congelada** a la
  fecha en que se generó el archivo: no se mueve por más que pase el tiempo.
- **`Estado a Hoy`** — se recalcula contra `TODAY()` cada vez que se abre el informe.
  Como ninguna guía tiene recibido y todas las fechas límite son del 2 al 7 de
  septiembre de 2026, **hoy las 183 salen como vencidas**. Es correcto según los datos,
  no un error del informe.

Diligenciar `Fecha recibido` en el Excel es lo que convierte la página de Cumplimiento
en una medición real. Mientras tanto, la tarjeta *Sin fecha de recibido* (183) es el
indicador honesto.

## Medidas

37 medidas en la tabla `_Medidas`, agrupadas en carpetas:

- **01 Volumen** — Guías, Planillas, Clientes Atendidos, Rutas Atendidas, Peso Total KG, Peso Promedio KG, Guías por Planilla, Peso por Planilla
- **02 Transporte** — Transportadores Activos, Placas Activas, Guías por Placa
- **03 Cumplimiento (a hoy)** — recalculado contra la fecha actual: Guías Recibidas, Guías sin Confirmar, % Sin Confirmar, Guías Vencidas, % Vencidas, Peso Vencido KG, Días de Mora (prom / máx / total)
- **04 Cumplimiento (Excel)** — según el semáforo congelado: Guías Vencidas / Por Vencer / En Plazo (Excel), % Vencidas (Excel), Días de Mora Origen (total)
- **05 Devoluciones** — Devoluciones, Unidades Devueltas, Peso Devuelto KG, Valor Devoluciones, % Peso Devuelto, Días de Gestión (prom)
- **06 Calidad de datos** — Guías sin Ciudad, sin Ruta, con Peso Cero, con Cliente Fuera del Maestro, con Alerta de Datos, % Guías con Alerta

## Qué dicen los datos actuales

Período del 31 de agosto al 3 de septiembre de 2026: 183 guías, 68 planillas,
231.598 kg, 105 clientes, 31 rutas, 39 vehículos.

- **GOLDEN mueve el 57 % de los kilos** (131.391 kg en 124 guías). Le siguen TACMO
  (41.201 kg en solo 11 guías, las cargas más pesadas) y CG CARGA (26.532 kg).
- **Bogotá y San Andrés concentran el 67 % del peso** (78.946 y 77.050 kg).
- **3 guías salieron con peso 0 kg**, las tres de FERTRANS en la planilla 9100.
- **1 cliente despachado no existe en el maestro**: `TRIANA BRACAMONTE MARIA ALEJANDRA`.
- **22.098 kg viajaron a guías sin ciudad registrada.**

## Regenerar el proyecto

El proyecto entero sale de los scripts de `tools/`, de modo que los nombres de
tabla, columna y medida no pueden desincronizarse entre modelo e informe:

```bash
python3 powerbi/tools/generar_pbip.py                              # regenera el PBIP
python3 powerbi/tools/validar.py powerbi/datos/GESTOAGRO_PowerBI_datos.xlsx
python3 powerbi/tools/verificar_proyecto.py powerbi/GESTOAGRO
```

- `modelo.py` — consultas M · `tablas.py` — tipos y relaciones · `medidas.py` — DAX
- `validar.py` — simula los pasos M y comprueba que cada columna citada exista en el libro
- `verificar_proyecto.py` — comprueba que todo JSON parsee y que las 70 referencias del informe resuelvan contra el modelo

Si editas el informe en Power BI Desktop, los cambios quedan en los archivos del
proyecto; volver a correr el generador los sobrescribe.

## Limitaciones

Este proyecto se generó y verificó de forma programática, **pero no se abrió en
Power BI Desktop** (el entorno donde se creó es Linux y no puede ejecutarlo). Las
comprobaciones automáticas cubren la estructura y la coherencia de referencias, no
el renderizado. Si alguna página no carga, lo más probable es un detalle de esquema
en un visual concreto: el modelo semántico es independiente del informe y se puede
abrir por su cuenta.
