# -*- coding: utf-8 -*-
"""Columnas calculadas y medidas DAX del modelo.

Todo el DAX se escribe en una sola linea a proposito: TMDL admite bloques
multilinea, pero la forma de una linea evita problemas de indentacion al
regenerar el proyecto. Power BI Desktop lo reformatea al editarlo.
"""

# (nombre, dax, tipo, formatString, sortByColumn, descripcion)
COLUMNAS_CALCULADAS = [
    (
        "Estado a Hoy",
        'SWITCH(TRUE(), NOT ISBLANK(Fact_Guias[Fecha Recibido]) && Fact_Guias[Fecha Recibido] <= Fact_Guias[Fecha Límite], "Cumplido en plazo", NOT ISBLANK(Fact_Guias[Fecha Recibido]), "Cumplido con mora", TODAY() > Fact_Guias[Fecha Límite], "Vencido", TODAY() = Fact_Guias[Fecha Límite], "Vence hoy", "En plazo")',
        "string",
        None,
        "Estado a Hoy Orden",
        "Estado recalculado contra la fecha actual. A diferencia de 'Semáforo Origen', se actualiza cada vez que se abre el informe.",
    ),
    (
        "Estado a Hoy Orden",
        'SWITCH(Fact_Guias[Estado a Hoy], "Cumplido en plazo", 1, "Cumplido con mora", 2, "En plazo", 3, "Vence hoy", 4, "Vencido", 5, 9)',
        "int64",
        "0",
        None,
        "Orden de presentación del estado, de mejor a peor.",
    ),
    (
        "Días de Mora",
        "MAX(0, INT(COALESCE(Fact_Guias[Fecha Recibido], TODAY()) - Fact_Guias[Fecha Límite]))",
        "int64",
        "0",
        None,
        "Días entre la fecha límite y la de recibido; si no hay recibido, se cuenta contra hoy.",
    ),
    (
        "Rango de Peso",
        'SWITCH(TRUE(), Fact_Guias[Peso KG] = 0, "00 · Sin peso", Fact_Guias[Peso KG] < 100, "01 · Menos de 100 kg", Fact_Guias[Peso KG] < 500, "02 · 100 a 500 kg", Fact_Guias[Peso KG] < 1000, "03 · 500 a 1.000 kg", Fact_Guias[Peso KG] < 5000, "04 · 1.000 a 5.000 kg", "05 · Más de 5.000 kg")',
        "string",
        None,
        None,
        "Tramo de peso de la guía.",
    ),
]

# (nombre, dax, formatString, carpeta, descripcion)
MEDIDAS = [
    # --- Volumen ---
    ("Guías", "COUNTROWS(Fact_Guias)", "#,0", "01 Volumen",
     "Número de guías (una fila por planilla + pedido + factura)."),
    ("Planillas", "DISTINCTCOUNT(Fact_Guias[Planilla])", "#,0", "01 Volumen",
     "Planillas distintas despachadas."),
    ("Clientes Atendidos", "DISTINCTCOUNT(Fact_Guias[ClienteKey])", "#,0", "01 Volumen",
     "Clientes distintos con al menos una guía."),
    ("Rutas Atendidas", "DISTINCTCOUNT(Fact_Guias[Ruta])", "#,0", "01 Volumen",
     "Rutas distintas cubiertas."),
    ("Peso Total KG", "SUM(Fact_Guias[Peso KG])", "#,0", "01 Volumen",
     "Kilos despachados."),
    ("Peso Promedio KG", "AVERAGE(Fact_Guias[Peso KG])", "#,0.0", "01 Volumen",
     "Kilos promedio por guía."),
    ("Guías por Planilla", "DIVIDE([Guías], [Planillas])", "#,0.0", "01 Volumen",
     "Guías promedio que lleva cada planilla."),
    ("Peso por Planilla", "DIVIDE([Peso Total KG], [Planillas])", "#,0", "01 Volumen",
     "Kilos promedio por planilla."),

    # --- Transporte ---
    ("Transportadores Activos", "DISTINCTCOUNT(Fact_Guias[Transportador])", "#,0", "02 Transporte",
     "Conductores distintos con despachos."),
    ("Placas Activas", "DISTINCTCOUNT(Fact_Guias[Placa])", "#,0", "02 Transporte",
     "Vehículos distintos usados."),
    ("Guías por Placa", "DIVIDE([Guías], [Placas Activas])", "#,0.0", "02 Transporte",
     "Guías promedio por vehículo."),

    # --- Cumplimiento recalculado a hoy ---
    ("Guías Recibidas", "CALCULATE([Guías], NOT ISBLANK(Fact_Guias[Fecha Recibido]))", "#,0", "03 Cumplimiento (a hoy)",
     "Guías con fecha de recibido registrada."),
    ("Guías sin Confirmar", "CALCULATE([Guías], ISBLANK(Fact_Guias[Fecha Recibido]))", "#,0", "03 Cumplimiento (a hoy)",
     "Guías sin fecha de recibido: no se sabe si llegaron."),
    ("% Sin Confirmar", "DIVIDE([Guías sin Confirmar], [Guías])", "0.0%", "03 Cumplimiento (a hoy)",
     "Proporción de guías sin confirmación de entrega."),
    ("Guías Vencidas", 'CALCULATE([Guías], Fact_Guias[Estado a Hoy] = "Vencido")', "#,0", "03 Cumplimiento (a hoy)",
     "Guías cuya fecha límite ya pasó y siguen sin recibido."),
    ("% Vencidas", "DIVIDE([Guías Vencidas], [Guías])", "0.0%", "03 Cumplimiento (a hoy)",
     "Proporción de guías vencidas a la fecha de hoy."),
    ("Peso Vencido KG", 'CALCULATE([Peso Total KG], Fact_Guias[Estado a Hoy] = "Vencido")', "#,0", "03 Cumplimiento (a hoy)",
     "Kilos comprometidos en guías vencidas."),
    ("Días de Mora (prom)", "AVERAGE(Fact_Guias[Días de Mora])", "#,0.0", "03 Cumplimiento (a hoy)",
     "Días de mora promedio por guía."),
    ("Días de Mora (máx)", "MAX(Fact_Guias[Días de Mora])", "#,0", "03 Cumplimiento (a hoy)",
     "Peor caso de mora."),
    ("Días de Mora (total)", "SUM(Fact_Guias[Días de Mora])", "#,0", "03 Cumplimiento (a hoy)",
     "Suma de días de mora, útil para priorizar rutas."),

    # --- Cumplimiento segun el semaforo congelado del Excel ---
    ("Guías Vencidas (Excel)", 'CALCULATE([Guías], Fact_Guias[Semáforo Origen] = "VENCIDO")', "#,0", "04 Cumplimiento (Excel)",
     "Vencidas según la columna Semáforo del archivo, congelada a su fecha de creación."),
    ("Guías Por Vencer (Excel)", 'CALCULATE([Guías], Fact_Guias[Semáforo Origen] = "Por vencer")', "#,0", "04 Cumplimiento (Excel)",
     "Por vencer según la columna Semáforo del archivo."),
    ("Guías En Plazo (Excel)", 'CALCULATE([Guías], Fact_Guias[Semáforo Origen] = "En plazo")', "#,0", "04 Cumplimiento (Excel)",
     "En plazo según la columna Semáforo del archivo."),
    ("% Vencidas (Excel)", "DIVIDE([Guías Vencidas (Excel)], [Guías])", "0.0%", "04 Cumplimiento (Excel)",
     "Proporción de vencidas según el semáforo del archivo."),
    ("Días de Mora Origen (total)", "SUM(Fact_Guias[Días Mora Origen])", "#,0", "04 Cumplimiento (Excel)",
     "Días de mora tal como venían calculados en el archivo."),

    # --- Devoluciones ---
    ("Devoluciones", "COALESCE(COUNTROWS(Fact_Devoluciones), 0)", "#,0", "05 Devoluciones",
     "Líneas de devolución registradas."),
    ("Unidades Devueltas", "SUM(Fact_Devoluciones[Cantidad Devuelta])", "#,0", "05 Devoluciones",
     "Unidades devueltas."),
    ("Peso Devuelto KG", "SUM(Fact_Devoluciones[Peso Devuelto KG])", "#,0", "05 Devoluciones",
     "Kilos devueltos."),
    ("Valor Devoluciones", "SUM(Fact_Devoluciones[Valor Devolución])", '"$"#,0', "05 Devoluciones",
     "Valor de las devoluciones."),
    ("% Peso Devuelto", "DIVIDE([Peso Devuelto KG], [Peso Total KG])", "0.00%", "05 Devoluciones",
     "Kilos devueltos sobre kilos despachados."),
    ("Días de Gestión (prom)", "AVERAGE(Fact_Devoluciones[Días de Gestión])", "#,0.0", "05 Devoluciones",
     "Días promedio para cerrar una devolución."),

    # --- Calidad de datos ---
    ("Guías sin Ciudad", 'CALCULATE([Guías], Fact_Guias[Ciudad] = "SIN CIUDAD")', "#,0", "06 Calidad de datos",
     "Guías sin ciudad ni en la guía ni en el maestro de clientes."),
    ("Guías sin Ruta", 'CALCULATE([Guías], Fact_Guias[Ruta] = "SIN RUTA")', "#,0", "06 Calidad de datos",
     "Guías sin ruta asignada."),
    ("Guías con Peso Cero", "CALCULATE([Guías], Fact_Guias[Peso KG] = 0)", "#,0", "06 Calidad de datos",
     "Guías despachadas con peso 0 kg."),
    ("Guías con Cliente Fuera del Maestro", "CALCULATE([Guías], Fact_Guias[Cliente en Maestro] = FALSE())", "#,0", "06 Calidad de datos",
     "Guías cuyo nombre de cliente no aparece en Dim_Clientes."),
    ("Guías con Alerta de Datos", 'CALCULATE([Guías], FILTER(Fact_Guias, Fact_Guias[Ciudad] = "SIN CIUDAD" || Fact_Guias[Ruta] = "SIN RUTA" || Fact_Guias[Peso KG] = 0 || Fact_Guias[Cliente en Maestro] = FALSE()))', "#,0", "06 Calidad de datos",
     "Guías con al menos un problema de datos."),
    ("% Guías con Alerta", "DIVIDE([Guías con Alerta de Datos], [Guías])", "0.0%", "06 Calidad de datos",
     "Proporción de guías con algún dato incompleto."),
]
