# -*- coding: utf-8 -*-
"""Genera el proyecto Power BI (PBIP): modelo TMDL + informe PBIR.

Uso:  python3 powerbi/tools/generar_pbip.py [carpeta_destino]

Todo el proyecto sale de este script, asi que los nombres de tabla, columna y
medida no pueden desincronizarse entre el modelo y el informe.
"""
import json
import os
import re
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import medidas as MED
import modelo as MOD
import tablas as TAB

NOMBRE = "GESTOAGRO"
CULTURA = "es-CO"
ANCHO, ALTO = 1280, 720

IDENT_SIMPLE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def q(nombre):
    """Cita un identificador TMDL si no es un identificador simple."""
    return nombre if IDENT_SIMPLE.match(nombre) else "'" + nombre.replace("'", "''") + "'"


def bloque_m(m, tabs):
    """Indenta una consulta M dentro de un bloque source = de TMDL."""
    pad = "\t" * tabs
    return "\n".join(pad + l if l.strip() else "" for l in m.splitlines())


def desc(texto, tabs=1):
    if not texto:
        return ""
    pad = "\t" * tabs
    return "".join(f"{pad}/// {l}\n" for l in texto.splitlines())


# --------------------------------------------------------------------------
# Modelo semantico (TMDL)
# --------------------------------------------------------------------------

M_POR_TABLA = {
    "Fact_Guias": MOD.M_FACT_GUIAS,
    "Dim_Clientes": MOD.M_DIM_CLIENTES,
    "Dim_Productos": MOD.M_DIM_PRODUCTOS,
    "Dim_Calendario": MOD.M_DIM_CALENDARIO,
    "Dim_Transportadora": MOD.M_DIM_TRANSPORTADORA,
    "Dim_Ruta": MOD.M_DIM_RUTA,
    "Fact_Devoluciones": MOD.M_FACT_DEVOLUCIONES,
    "_Medidas": MOD.M_MEDIDAS,
}

ORDEN_TABLAS = [
    "Fact_Guias", "Fact_Devoluciones", "Dim_Calendario", "Dim_Clientes",
    "Dim_Productos", "Dim_Transportadora", "Dim_Ruta", "_Medidas",
]

DESC_TABLA = {
    "Fact_Guias": "Una fila por guía despachada (planilla + pedido + factura). Une Fact_Despachos (peso y transporte) con Fact_Cumplidos (plazo y estado).",
    "Fact_Devoluciones": "Devoluciones de mercancía. La hoja de origen está vacía: la tabla existe con su estructura lista para cuando se empiece a diligenciar.",
    "Dim_Calendario": "Calendario de 2026, marcado como tabla de fechas del modelo.",
    "Dim_Clientes": "Maestro de clientes, deduplicado por nombre normalizado.",
    "Dim_Productos": "Catálogo de productos. Sin relación activa con las guías porque el detalle por producto solo aparece en devoluciones.",
    "Dim_Transportadora": "Empresas de transporte, derivadas de las guías.",
    "Dim_Ruta": "Rutas atendidas, derivadas de las guías.",
    "_Medidas": "Tabla técnica que agrupa todas las medidas del modelo.",
}


def tmdl_columna(tabla, col, calculada=None):
    nombre, tipo, fmt, oculta, sortby, d = col
    out = desc(d, 1)
    if calculada:
        out += f"\tcolumn {q(nombre)} = {calculada}\n"
    else:
        out += f"\tcolumn {q(nombre)}\n"
    out += f"\t\tdataType: {tipo}\n"
    if oculta:
        out += "\t\tisHidden\n"
    if tabla == "Dim_Calendario" and nombre == "Fecha":
        out += "\t\tisKey\n"
    if fmt:
        out += f"\t\tformatString: {fmt}\n"
    out += f"\t\tlineageTag: {MOD.lt(tabla, nombre)}\n"
    out += "\t\tsummarizeBy: none\n"
    if sortby:
        out += f"\t\tsortByColumn: {q(sortby)}\n"
    if not calculada:
        out += f"\t\tsourceColumn: {nombre}\n"
    out += "\n\t\tannotation SummarizationSetBy = Automatic\n"
    if tipo == "dateTime":
        out += "\n\t\tannotation UnderlyingDateTimeDataType = Date\n"
    return out + "\n"


def tmdl_medida(m):
    nombre, dax, fmt, carpeta, d = m
    out = desc(d, 1)
    out += f"\tmeasure {q(nombre)} = {dax}\n"
    if fmt:
        out += f"\t\tformatString: {fmt}\n"
    out += f"\t\tdisplayFolder: {carpeta}\n"
    out += f"\t\tlineageTag: {MOD.lt('_Medidas', nombre)}\n"
    return out + "\n"


def tmdl_tabla(tabla):
    out = desc(DESC_TABLA.get(tabla), 0)
    out += f"table {q(tabla)}\n"
    if tabla == "Dim_Calendario":
        out += "\tdataCategory: Time\n"
    out += f"\tlineageTag: {MOD.lt('table', tabla)}\n\n"

    if tabla == "_Medidas":
        for m in MED.MEDIDAS:
            out += tmdl_medida(m)

    calc = {c[0]: c for c in MED.COLUMNAS_CALCULADAS} if tabla == "Fact_Guias" else {}
    for col in TAB.TABLAS[tabla]:
        out += tmdl_columna(tabla, col)
    for nombre, dax, tipo, fmt, sortby, d in MED.COLUMNAS_CALCULADAS:
        if tabla == "Fact_Guias":
            out += tmdl_columna(tabla, (nombre, tipo, fmt, False, sortby, d), calculada=dax)

    out += f"\tpartition {q(tabla)} = m\n\t\tmode: import\n\t\tsource =\n"
    out += bloque_m(M_POR_TABLA[tabla], 4) + "\n\n"
    out += "\tannotation PBI_ResultType = Table\n"
    return out


def escribir_modelo(base):
    sm = os.path.join(base, f"{NOMBRE}.SemanticModel")
    defi = os.path.join(sm, "definition")
    os.makedirs(os.path.join(defi, "tables"), exist_ok=True)

    esc(os.path.join(sm, ".platform"), json.dumps({
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/gitIntegration/platformProperties/2.0.0/schema.json",
        "metadata": {"type": "SemanticModel", "displayName": NOMBRE},
        "config": {"version": "2.0", "logicalId": MOD.lt("logical", "semanticmodel")},
    }, indent=2, ensure_ascii=False))

    esc(os.path.join(sm, "definition.pbism"), json.dumps(
        {"version": "4.2", "settings": {}}, indent=2))

    esc(os.path.join(defi, "database.tmdl"), "database\n\tcompatibilityLevel: 1567\n")

    mdl = f"model Model\n\tculture: {CULTURA}\n\tdefaultPowerBIDataSourceVersion: powerBI_V3\n"
    mdl += "\tdiscourageImplicitMeasures\n"
    mdl += f"\tsourceQueryCulture: {CULTURA}\n"
    mdl += "\tdataAccessOptions\n\t\tlegacyRedirects\n\t\treturnErrorValuesAsNull\n\n"
    orden = json.dumps(["RutaArchivo", "fnHoja"] + ORDEN_TABLAS, ensure_ascii=False)
    mdl += f"annotation PBI_QueryOrder = {orden}\n\n"
    mdl += "annotation __PBI_TimeIntelligenceEnabled = 0\n\n"
    for t in ORDEN_TABLAS:
        mdl += f"ref table {q(t)}\n"
    esc(os.path.join(defi, "model.tmdl"), mdl)

    exprs = desc("Ruta completa al libro de Excel con los datos. Cámbiala aquí si mueves el archivo.", 0)
    exprs += f'expression RutaArchivo = "{MOD.RUTA_DEFECTO}" meta [IsParameterQuery=true, Type="Text", IsParameterQueryRequired=true]\n'
    exprs += f"\tlineageTag: {MOD.lt('expr', 'RutaArchivo')}\n\n\tannotation PBI_ResultType = Text\n\n"
    exprs += desc("Lee una hoja del libro y promueve la primera fila a encabezados.", 0)
    exprs += "expression fnHoja =\n" + bloque_m(MOD.FN_HOJA, 2) + "\n"
    exprs += f"\tlineageTag: {MOD.lt('expr', 'fnHoja')}\n\n\tannotation PBI_ResultType = Function\n"
    esc(os.path.join(defi, "expressions.tmdl"), exprs)

    rel = ""
    for nombre, ft, fc, tt, tc, activa in TAB.RELACIONES:
        rel += f"relationship {nombre}\n"
        if not activa:
            rel += "\tisActive: false\n"
        rel += f"\tfromColumn: {q(ft)}.{q(fc)}\n"
        rel += f"\ttoColumn: {q(tt)}.{q(tc)}\n\n"
    esc(os.path.join(defi, "relationships.tmdl"), rel)

    for t in ORDEN_TABLAS:
        esc(os.path.join(defi, "tables", f"{t}.tmdl"), tmdl_tabla(t))


def esc(ruta, contenido):
    os.makedirs(os.path.dirname(ruta), exist_ok=True)
    with open(ruta, "w", encoding="utf-8", newline="\n") as f:
        f.write(contenido if contenido.endswith("\n") else contenido + "\n")


# --------------------------------------------------------------------------
# Informe (PBIR)
# --------------------------------------------------------------------------

ESQ = "https://developer.microsoft.com/json-schemas/fabric/item/report/definition"

MEDIDAS_SET = {m[0] for m in MED.MEDIDAS}
COLUMNAS_SET = set()
for _t, _cols in TAB.TABLAS.items():
    for _c in _cols:
        COLUMNAS_SET.add((_t, _c[0]))
for _c in MED.COLUMNAS_CALCULADAS:
    COLUMNAS_SET.add(("Fact_Guias", _c[0]))


def campo(ref):
    """'Tabla.Campo' -> proyeccion PBIR, resolviendo si es medida o columna."""
    tabla, prop = ref.split(".", 1)
    if tabla == "_Medidas":
        if prop not in MEDIDAS_SET:
            raise KeyError(f"medida inexistente: {ref}")
        f = {"Measure": {"Expression": {"SourceRef": {"Entity": tabla}}, "Property": prop}}
    else:
        if (tabla, prop) not in COLUMNAS_SET:
            raise KeyError(f"columna inexistente: {ref}")
        f = {"Column": {"Expression": {"SourceRef": {"Entity": tabla}}, "Property": prop}}
    return {"field": f, "queryRef": ref, "nativeQueryRef": prop}


def literal(texto):
    return {"expr": {"Literal": {"Value": "'" + texto.replace("'", "''") + "'"}}}


_contador = [0]


def visual(tipo, x, y, w, h, roles=None, titulo=None, orden=None, texto=None):
    _contador[0] += 1
    vid = f"v{_contador[0]:03d}"
    v = {"visualType": tipo}
    if roles:
        estado = {}
        for rol, refs in roles.items():
            estado[rol] = {"projections": [campo(r) for r in refs]}
        v["query"] = {"queryState": estado}
        if orden:
            ref, direccion = orden
            v["query"]["sortDefinition"] = {
                "sort": [{"field": campo(ref)["field"], "direction": direccion}],
                "isDefaultSort": True,
            }
    objetos = {}
    if titulo:
        objetos["title"] = [{"properties": {"text": literal(titulo), "show": {"expr": {"Literal": {"Value": "true"}}}}}]
    if texto is not None:
        objetos["general"] = [{"properties": {"paragraphs": texto}}]
    if objetos:
        v["objects"] = objetos
    if tipo != "textbox":
        v["drillFilterOtherVisuals"] = True
    return {
        "$schema": f"{ESQ}/visualContainer/1.4.0/schema.json",
        "name": vid,
        "position": {"x": x, "y": y, "z": _contador[0], "width": w, "height": h, "tabOrder": _contador[0]},
        "visual": v,
    }


def parrafo(texto, tam="12pt", peso="normal", color="#333333"):
    return [{"textRuns": [{"value": texto, "textStyle": {"fontSize": tam, "fontWeight": peso, "color": color}}]}]


def titulo_pagina(texto, subtitulo):
    return [
        visual("textbox", 16, 12, 1248, 40, texto=parrafo(texto, "20pt", "bold", "#1F3864")),
        visual("textbox", 16, 54, 1248, 24, texto=parrafo(subtitulo, "11pt", "normal", "#666666")),
    ]


def fila_tarjetas(refs, y=84, x0=16, ancho=1248, alto=96, sep=8):
    n = len(refs)
    w = (ancho - sep * (n - 1)) // n
    return [
        visual("card", x0 + i * (w + sep), y, w, alto, {"Values": [r]}, titulo=t)
        for i, (r, t) in enumerate(refs)
    ]


def paginas():
    """Devuelve [(id, nombre, [visuales])]."""
    P = []

    # ---------------- 1. Resumen ejecutivo ----------------
    v = titulo_pagina(
        "Operación de despachos · GESTOAGRO",
        "183 guías despachadas entre el 31 de agosto y el 3 de septiembre de 2026. Use los filtros de la izquierda para acotar el análisis.",
    )
    v += fila_tarjetas([
        ("_Medidas.Guías", "Guías"),
        ("_Medidas.Peso Total KG", "Kilos despachados"),
        ("_Medidas.Planillas", "Planillas"),
        ("_Medidas.Clientes Atendidos", "Clientes"),
        ("_Medidas.Rutas Atendidas", "Rutas"),
        ("_Medidas.% Sin Confirmar", "Sin confirmar entrega"),
    ])
    v += [
        visual("slicer", 16, 192, 236, 200, {"Values": ["Dim_Calendario.Fecha"]}, titulo="Fecha de despacho"),
        visual("slicer", 16, 400, 236, 304, {"Values": ["Dim_Transportadora.Transportadora"]}, titulo="Transportadora"),
        visual("donutChart", 260, 192, 400, 300,
               {"Category": ["Fact_Guias.Semáforo Origen"], "Y": ["_Medidas.Guías"]},
               titulo="Semáforo del archivo (estado al generarlo)"),
        visual("clusteredColumnChart", 668, 192, 596, 300,
               {"Category": ["Dim_Transportadora.Transportadora"], "Y": ["_Medidas.Peso Total KG"]},
               titulo="Kilos por transportadora",
               orden=("_Medidas.Peso Total KG", "Descending")),
        visual("lineChart", 260, 500, 400, 204,
               {"Category": ["Dim_Calendario.Fecha"], "Y": ["_Medidas.Peso Total KG"]},
               titulo="Kilos por día de despacho"),
        visual("clusteredBarChart", 668, 500, 596, 204,
               {"Category": ["Dim_Ruta.Ruta"], "Y": ["_Medidas.Guías"]},
               titulo="Guías por ruta",
               orden=("_Medidas.Guías", "Descending")),
    ]
    P.append(("resumen", "Resumen ejecutivo", v))

    # ---------------- 2. Cumplimiento ----------------
    v = titulo_pagina(
        "Cumplimiento de entregas",
        "Arriba, el estado recalculado contra la fecha de hoy. Abajo, el semáforo tal como venía en el archivo.",
    )
    v += fila_tarjetas([
        ("_Medidas.Guías sin Confirmar", "Sin fecha de recibido"),
        ("_Medidas.Guías Vencidas", "Vencidas hoy"),
        ("_Medidas.% Vencidas", "% vencidas hoy"),
        ("_Medidas.Días de Mora (total)", "Días de mora acumulados"),
        ("_Medidas.Días de Mora (máx)", "Peor mora"),
    ])
    v += [
        visual("textbox", 16, 192, 1248, 44, texto=parrafo(
            "Ninguna de las 183 guías tiene fecha de recibido, así que a la fecha de hoy todas se calculan como vencidas. "
            "Diligencie 'Fecha recibido' en el Excel para que estas tarjetas midan cumplimiento real.",
            "11pt", "bold", "#B03A2E")),
        visual("stackedBarChart", 16, 244, 624, 232,
               {"Category": ["Dim_Transportadora.Transportadora"], "Y": ["_Medidas.Guías"],
                "Series": ["Fact_Guias.Semáforo Origen"]},
               titulo="Semáforo del archivo por transportadora"),
        visual("clusteredBarChart", 648, 244, 616, 232,
               {"Category": ["Dim_Ruta.Ruta"], "Y": ["_Medidas.Días de Mora Origen (total)"]},
               titulo="Días de mora del archivo por ruta",
               orden=("_Medidas.Días de Mora Origen (total)", "Descending")),
        visual("tableEx", 16, 484, 1248, 220,
               {"Values": ["Fact_Guias.GuiaID", "Fact_Guias.Cliente", "Fact_Guias.Ciudad",
                           "Fact_Guias.Ruta", "Fact_Guias.Transportadora", "Fact_Guias.Fecha Despacho",
                           "Fact_Guias.Fecha Límite", "Fact_Guias.Semáforo Origen",
                           "_Medidas.Días de Mora Origen (total)"]},
               titulo="Detalle de guías"),
    ]
    P.append(("cumplimiento", "Cumplimiento", v))

    # ---------------- 3. Transporte ----------------
    v = titulo_pagina(
        "Transportadoras, conductores y vehículos",
        "Reparto de la carga entre flota propia y terceros.",
    )
    v += fila_tarjetas([
        ("_Medidas.Transportadores Activos", "Conductores"),
        ("_Medidas.Placas Activas", "Vehículos"),
        ("_Medidas.Guías por Placa", "Guías por vehículo"),
        ("_Medidas.Peso por Planilla", "Kilos por planilla"),
        ("_Medidas.Guías por Planilla", "Guías por planilla"),
    ])
    v += [
        visual("slicer", 16, 192, 236, 160, {"Values": ["Dim_Transportadora.Tipo Transportadora"]},
               titulo="Tipo de transportadora"),
        visual("slicer", 16, 360, 236, 344, {"Values": ["Dim_Ruta.Zona"]}, titulo="Zona"),
        visual("clusteredColumnChart", 260, 192, 500, 260,
               {"Category": ["Dim_Transportadora.Tipo Transportadora"], "Y": ["_Medidas.Peso Total KG"]},
               titulo="Kilos por tipo de transportadora"),
        visual("clusteredBarChart", 768, 192, 496, 260,
               {"Category": ["Fact_Guias.Transportador"], "Y": ["_Medidas.Guías"]},
               titulo="Guías por conductor",
               orden=("_Medidas.Guías", "Descending")),
        visual("tableEx", 260, 460, 1004, 244,
               {"Values": ["Dim_Transportadora.Transportadora", "Dim_Transportadora.Tipo Transportadora",
                           "_Medidas.Guías", "_Medidas.Planillas", "_Medidas.Peso Total KG",
                           "_Medidas.Peso Promedio KG", "_Medidas.Placas Activas"]},
               titulo="Resumen por transportadora",
               orden=("_Medidas.Peso Total KG", "Descending")),
    ]
    P.append(("transporte", "Transporte", v))

    # ---------------- 4. Clientes y ciudades ----------------
    v = titulo_pagina(
        "Clientes y destinos",
        "Dónde se concentra el peso despachado.",
    )
    v += fila_tarjetas([
        ("_Medidas.Clientes Atendidos", "Clientes"),
        ("_Medidas.Guías", "Guías"),
        ("_Medidas.Peso Total KG", "Kilos"),
        ("_Medidas.Peso Promedio KG", "Kilos por guía"),
    ])
    v += [
        visual("slicer", 16, 192, 236, 512, {"Values": ["Fact_Guias.Ciudad"]}, titulo="Ciudad"),
        visual("clusteredBarChart", 260, 192, 500, 260,
               {"Category": ["Fact_Guias.Ciudad"], "Y": ["_Medidas.Peso Total KG"]},
               titulo="Kilos por ciudad",
               orden=("_Medidas.Peso Total KG", "Descending")),
        visual("clusteredBarChart", 768, 192, 496, 260,
               {"Category": ["Fact_Guias.Cliente"], "Y": ["_Medidas.Peso Total KG"]},
               titulo="Kilos por cliente",
               orden=("_Medidas.Peso Total KG", "Descending")),
        visual("tableEx", 260, 460, 1004, 244,
               {"Values": ["Fact_Guias.Cliente", "Fact_Guias.Ciudad", "Fact_Guias.Vendedor",
                           "_Medidas.Guías", "_Medidas.Peso Total KG", "_Medidas.Guías sin Confirmar"]},
               titulo="Detalle por cliente",
               orden=("_Medidas.Peso Total KG", "Descending")),
    ]
    P.append(("clientes", "Clientes y destinos", v))

    # ---------------- 5. Devoluciones ----------------
    v = titulo_pagina(
        "Devoluciones",
        "Página lista para usar: hoy no tiene datos porque la hoja Fact_Devoluciones del Excel está vacía.",
    )
    v += fila_tarjetas([
        ("_Medidas.Devoluciones", "Devoluciones"),
        ("_Medidas.Unidades Devueltas", "Unidades"),
        ("_Medidas.Peso Devuelto KG", "Kilos devueltos"),
        ("_Medidas.Valor Devoluciones", "Valor"),
        ("_Medidas.% Peso Devuelto", "% sobre lo despachado"),
    ])
    v += [
        visual("textbox", 16, 192, 1248, 44, texto=parrafo(
            "Los visuales de abajo quedarán poblados en cuanto se registren devoluciones en el Excel; "
            "la estructura de la hoja ya está mapeada en el modelo.", "11pt", "normal", "#666666")),
        visual("clusteredBarChart", 16, 244, 624, 240,
               {"Category": ["Fact_Devoluciones.Motivo Devolución"], "Y": ["_Medidas.Peso Devuelto KG"]},
               titulo="Kilos devueltos por motivo",
               orden=("_Medidas.Peso Devuelto KG", "Descending")),
        visual("clusteredColumnChart", 648, 244, 616, 240,
               {"Category": ["Fact_Devoluciones.Estado"], "Y": ["_Medidas.Devoluciones"]},
               titulo="Devoluciones por estado"),
        visual("tableEx", 16, 492, 1248, 212,
               {"Values": ["Fact_Devoluciones.Fecha Registro", "Fact_Devoluciones.Cliente",
                           "Fact_Devoluciones.Descripción Producto", "Fact_Devoluciones.Motivo Devolución",
                           "_Medidas.Unidades Devueltas", "_Medidas.Peso Devuelto KG",
                           "_Medidas.Valor Devoluciones", "_Medidas.Días de Gestión (prom)"]},
               titulo="Detalle de devoluciones"),
    ]
    P.append(("devoluciones", "Devoluciones", v))

    # ---------------- 6. Calidad de datos ----------------
    v = titulo_pagina(
        "Calidad de los datos",
        "Qué hay que corregir en el Excel para que el informe mida cumplimiento de verdad.",
    )
    v += fila_tarjetas([
        ("_Medidas.Guías sin Confirmar", "Sin fecha de recibido"),
        ("_Medidas.Guías sin Ciudad", "Sin ciudad"),
        ("_Medidas.Guías sin Ruta", "Sin ruta"),
        ("_Medidas.Guías con Peso Cero", "Peso 0 kg"),
        ("_Medidas.Guías con Cliente Fuera del Maestro", "Cliente sin maestro"),
        ("_Medidas.% Guías con Alerta", "% con alguna alerta"),
    ])
    v += [
        visual("textbox", 16, 192, 1248, 60, texto=parrafo(
            "El maestro de clientes traía 9 nombres repetidos con códigos distintos (errores de digitación); "
            "el modelo conserva uno por nombre para poder relacionarlo. Corregir esos códigos en el origen "
            "evita que se repartan las ventas de un mismo cliente.", "11pt", "normal", "#666666")),
        visual("clusteredColumnChart", 16, 260, 624, 220,
               {"Category": ["Fact_Guias.Origen Ciudad"], "Y": ["_Medidas.Guías"]},
               titulo="De dónde sale la ciudad de cada guía"),
        visual("clusteredColumnChart", 648, 260, 616, 220,
               {"Category": ["Fact_Guias.Rango de Peso"], "Y": ["_Medidas.Guías"]},
               titulo="Guías por tramo de peso"),
        visual("tableEx", 16, 488, 1248, 216,
               {"Values": ["Fact_Guias.GuiaID", "Fact_Guias.Cliente", "Fact_Guias.Cliente en Maestro",
                           "Fact_Guias.Ciudad", "Fact_Guias.Origen Ciudad", "Fact_Guias.Ruta",
                           "Fact_Guias.Peso KG", "Fact_Guias.Fecha Recibido"]},
               titulo="Guías para revisar"),
    ]
    P.append(("calidad", "Calidad de datos", v))

    return P


def escribir_informe(base):
    rp = os.path.join(base, f"{NOMBRE}.Report")
    defi = os.path.join(rp, "definition")
    os.makedirs(defi, exist_ok=True)

    esc(os.path.join(rp, ".platform"), json.dumps({
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/gitIntegration/platformProperties/2.0.0/schema.json",
        "metadata": {"type": "Report", "displayName": NOMBRE},
        "config": {"version": "2.0", "logicalId": MOD.lt("logical", "report")},
    }, indent=2, ensure_ascii=False))

    esc(os.path.join(rp, "definition.pbir"), json.dumps({
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definitionProperties/1.0.0/schema.json",
        "version": "4.0",
        "datasetReference": {"byPath": {"path": f"../{NOMBRE}.SemanticModel"}},
    }, indent=2))

    esc(os.path.join(defi, "report.json"), json.dumps({
        "$schema": f"{ESQ}/report/1.0.0/schema.json",
        "layoutOptimization": "None",
    }, indent=2))

    pgs = paginas()
    esc(os.path.join(defi, "pages", "pages.json"), json.dumps({
        "$schema": f"{ESQ}/pagesMetadata/1.0.0/schema.json",
        "pageOrder": [p[0] for p in pgs],
        "activePageName": pgs[0][0],
    }, indent=2))

    for pid, nombre, visuales in pgs:
        esc(os.path.join(defi, "pages", pid, "page.json"), json.dumps({
            "$schema": f"{ESQ}/page/1.4.0/schema.json",
            "name": pid,
            "displayName": nombre,
            "displayOption": "FitToPage",
            "height": ALTO,
            "width": ANCHO,
        }, indent=2, ensure_ascii=False))
        for vis in visuales:
            esc(os.path.join(defi, "pages", pid, "visuals", vis["name"], "visual.json"),
                json.dumps(vis, indent=2, ensure_ascii=False))


def main():
    destino = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "GESTOAGRO")
    for sub in (f"{NOMBRE}.SemanticModel", f"{NOMBRE}.Report"):
        ruta = os.path.join(destino, sub)
        if os.path.isdir(ruta):
            shutil.rmtree(ruta)
    os.makedirs(destino, exist_ok=True)

    esc(os.path.join(destino, f"{NOMBRE}.pbip"), json.dumps({
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/pbip/1.0.0/schema.json",
        "version": "1.0",
        "artifacts": [{"report": {"path": f"{NOMBRE}.Report"}}],
        "settings": {"enableAutoRecovery": True},
    }, indent=2))

    escribir_modelo(destino)
    escribir_informe(destino)

    n = sum(len(p[2]) for p in paginas())
    print(f"Proyecto generado en {destino}")
    print(f"  tablas: {len(ORDEN_TABLAS)} | medidas: {len(MED.MEDIDAS)} | "
          f"columnas calculadas: {len(MED.COLUMNAS_CALCULADAS)} | relaciones: {len(TAB.RELACIONES)}")
    print(f"  páginas: {len(paginas())} | visuales: {n}")


if __name__ == "__main__":
    main()
