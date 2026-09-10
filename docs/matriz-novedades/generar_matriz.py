# -*- coding: utf-8 -*-
"""MATRIZ DE NOVEDADES - LOGISTICA Y TRANSPORTE

Reconstruye MATRIZ_NOVEDADES_LOGISTICA_TRANSPORTE.xlsx desde cero.
Registra novedades en ruta (con guia) e internas (sin guia).
Ver README.md para el detalle de columnas, formulas y KPIs.

    pip install openpyxl
    python3 generar_matriz.py
    python3 crear_ejemplo.py   # opcional: version con datos de muestra

Diseno propio basado en estandares de la industria:
OTIF/DIFOT, carrier scorecard, causa raiz 6M (Ishikawa), codigos de entrega fallida.
"""
import os, datetime
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side, Protection
from openpyxl.utils import column_index_from_string as ci, get_column_letter
from openpyxl.worksheet.datavalidation import DataValidation
from openpyxl.formatting.rule import FormulaRule, CellIsRule, DataBarRule
from openpyxl.workbook.defined_name import DefinedName

# ---------------- capacidad ----------------
ENV0, ENV1 = 4, 3003      # ENVIOS   : datos fila 4 a 3003
NOV0, NOV1 = 4, 1503      # NOVEDADES: datos fila 4 a 1503
CFG0, CFG1 = 4, 63        # CONFIG   : catalogos fila 4 a 63

E = lambda c: f"ENVIOS!${c}${ENV0}:${c}${ENV1}"
N = lambda c: f"NOVEDADES!${c}${NOV0}:${c}${NOV1}"
C = lambda c: f"CONFIG!${c}${CFG0}:${c}${CFG1}"

# ---------------- paleta moderna ----------------
INK      = "FF0F172A"   # slate-900  titulos
INK2     = "FF1E293B"   # slate-800  bandas
BLUE     = "FF2563EB"   # blue-600   encabezado calculado
AMBER    = "FFD97706"   # amber-600  encabezado manual
EDIT     = "FFFEF3C7"   # amber-100  celda que se digita
CALC     = "FFF8FAFC"   # slate-50   celda calculada
LINE     = "FFE2E8F0"   # slate-200  bordes
CARD     = "FFF1F5F9"   # slate-100  tarjetas
OK_BG,   OK_TX   = "FFDCFCE7", "FF166534"
WARN_BG, WARN_TX = "FFFEF9C3", "FF854D0E"
DANG_BG, DANG_TX = "FFFEE2E2", "FF991B1B"
INFO_BG, INFO_TX = "FFDBEAFE", "FF1E40AF"
MUTE_BG, MUTE_TX = "FFF1F5F9", "FF475569"
WHITE = "FFFFFFFF"

FN = "Calibri"
f_base  = Font(name=FN, size=10, color=INK)
f_bold  = Font(name=FN, size=10, bold=True, color=INK)
f_hdr   = Font(name=FN, size=10, bold=True, color=WHITE)
f_band  = Font(name=FN, size=9,  bold=True, color=WHITE)
f_title = Font(name=FN, size=18, bold=True, color=WHITE)
f_sec   = Font(name=FN, size=11, bold=True, color=WHITE)
f_note  = Font(name=FN, size=9,  italic=True, color=MUTE_TX)
f_kpi   = Font(name=FN, size=22, bold=True, color=INK)
f_kpil  = Font(name=FN, size=9,  bold=True, color=MUTE_TX)

fl = lambda c: PatternFill("solid", fgColor=c)
thin = Side(style="thin", color=LINE)
BOX  = Border(left=thin, right=thin, top=thin, bottom=thin)
CEN  = Alignment(horizontal="center", vertical="center", wrap_text=True)
LEF  = Alignment(horizontal="left",   vertical="center")
LEFW = Alignment(horizontal="left",   vertical="center", wrap_text=True)
RIG  = Alignment(horizontal="right",  vertical="center")

FECHA, MONEY, NUM, PCT, PCT1, DEC = "dd/mm/yyyy", '"$"#,##0', "#,##0", "0%", "0.0%", "#,##0.0"

wb = openpyxl.Workbook(); wb.remove(wb.active)

def sheet(name, tab):
    ws = wb.create_sheet(name); ws.sheet_properties.tabColor = tab
    ws.sheet_view.showGridLines = False
    return ws

def widths(ws, d):
    for k, v in d.items(): ws.column_dimensions[k].width = v

def put(ws, coord, val, font=None, fill=None, fmt=None, al=None, box=True, editable=False):
    c = ws[coord]; c.value = val
    c.font = font or f_base
    if fill: c.fill = fl(fill)
    if fmt: c.number_format = fmt
    c.alignment = al or LEF
    if box: c.border = BOX
    if editable: c.protection = Protection(locked=False)
    return c

def banner(ws, row, c0, c1, text, color=INK2):
    c = ws.cell(row=row, column=ci(c0), value=text)
    c.font = f_band; c.fill = fl(color); c.alignment = CEN
    ws.merge_cells(start_row=row, start_column=ci(c0), end_row=row, end_column=ci(c1))
    ws.row_dimensions[row].height = 17

def title(ws, row, c0, c1, text, h=34):
    c = ws.cell(row=row, column=ci(c0), value=text)
    c.font = f_title; c.fill = fl(INK); c.alignment = Alignment(horizontal="left", vertical="center", indent=1)
    ws.merge_cells(start_row=row, start_column=ci(c0), end_row=row, end_column=ci(c1))
    ws.row_dimensions[row].height = h

def seccion(ws, row, c0, c1, text):
    c = ws.cell(row=row, column=ci(c0), value=text)
    c.font = f_sec; c.fill = fl(INK2); c.alignment = Alignment(horizontal="left", vertical="center", indent=1)
    ws.merge_cells(start_row=row, start_column=ci(c0), end_row=row, end_column=ci(c1))
    ws.row_dimensions[row].height = 22

# =========================================================================
# CONFIG  -  catalogos y reglas de negocio
# =========================================================================
cf = sheet("CONFIG", "FF64748B")

TIPOS = [  # tipo, ambito, gravedad, SLA dias habiles, afecta la entrega (in full)
 # --- lo que pasa EN RUTA, con guia ---
 ("Cliente ausente / no atiende",              "En ruta", "Media",   2, "SÍ"),
 ("Cliente rechaza el envío",                  "En ruta", "Alta",    2, "SÍ"),
 ("Dirección errada o incompleta",             "En ruta", "Media",   2, "SÍ"),
 ("Cliente cerrado / fuera de horario",        "En ruta", "Media",   2, "SÍ"),
 ("Zona restringida o sin acceso",             "En ruta", "Media",   3, "SÍ"),
 ("Pago contraentrega fallido",                "En ruta", "Alta",    2, "SÍ"),
 ("Avería / producto dañado",                  "En ruta", "Alta",    3, "SÍ"),
 ("Faltante (llegó de menos)",                 "En ruta", "Alta",    2, "SÍ"),
 ("Sobrante (llegó de más)",                   "En ruta", "Baja",    5, "NO"),
 ("Producto equivocado",                       "En ruta", "Alta",    2, "SÍ"),
 ("Producto vencido o próximo a vencer",       "En ruta", "Alta",    3, "SÍ"),
 ("Empaque en mal estado",                     "En ruta", "Media",   3, "NO"),
 ("Retraso en vía",                            "En ruta", "Alta",    1, "NO"),
 ("Vehículo varado / falla mecánica",          "En ruta", "Crítica", 1, "SÍ"),
 ("Pérdida o robo de mercancía",               "En ruta", "Crítica", 1, "SÍ"),
 ("Entrega parcial acordada",                  "En ruta", "Baja",    5, "SÍ"),
 ("Soporte de entrega sin firmar",             "En ruta", "Media",   4, "NO"),
 ("Error en factura o precio",                 "En ruta", "Media",   5, "NO"),
 ("Flete no liquidado",                        "En ruta", "Baja",    5, "NO"),
 # --- lo que pasa DENTRO DE LA EMPRESA, sin guia ---
 ("Error de alistamiento detectado en bodega", "Interna", "Media",   1, "NO"),
 ("Diferencia de inventario",                  "Interna", "Alta",    3, "NO"),
 ("Producto averiado en bodega",               "Interna", "Alta",    2, "NO"),
 ("Producto vencido en bodega",                "Interna", "Alta",    3, "NO"),
 ("Derrame o daño en manipulación interna",    "Interna", "Alta",    2, "NO"),
 ("Demora en el cargue",                       "Interna", "Media",   1, "NO"),
 ("Demora en facturación o documentos",        "Interna", "Media",   2, "NO"),
 ("Pedido mal digitado (antes del despacho)",  "Interna", "Media",   1, "NO"),
 ("Devolución recibida sin soporte",           "Interna", "Media",   3, "NO"),
 ("Falla de equipo en bodega",                 "Interna", "Alta",    1, "NO"),
 ("Faltante de personal en el turno",          "Interna", "Media",   1, "NO"),
 ("Incidente de seguridad o accidente laboral","Interna", "Crítica", 1, "NO"),
]
CAUSAS = [  # causa raiz, familia 6M, area responsable
 ("Error de alistamiento (picking)",            "Método",        "Bodega"),
 ("Embalaje o estibado deficiente",             "Material",      "Bodega"),
 ("Inventario descuadrado",                     "Medición",      "Bodega"),
 ("Falta de espacio u orden en bodega",         "Método",        "Bodega"),
 ("Personal insuficiente en el turno",          "Mano de obra",  "Bodega"),
 ("Equipo de bodega fuera de servicio",         "Máquina",       "Bodega"),
 ("Manipulación brusca en cargue/descargue",    "Mano de obra",  "Transporte"),
 ("Sobrecupo o mal acomodo en el vehículo",     "Método",        "Transporte"),
 ("Conductor sin capacitación o procedimiento", "Mano de obra",  "Transporte"),
 ("Falla mecánica del vehículo",                "Máquina",       "Transporte"),
 ("Ruta mal planeada o secuencia errada",       "Método",        "Planeación"),
 ("Promesa de entrega irreal",                  "Método",        "Planeación"),
 ("Procedimiento no seguido",                   "Método",        "Operaciones"),
 ("Datos del cliente desactualizados",          "Medición",      "Comercial"),
 ("Error de digitación del pedido",             "Mano de obra",  "Comercial"),
 ("Cliente cambió de decisión",                 "Externo",       "Comercial"),
 ("Documentación incompleta",                   "Método",        "Facturación"),
 ("Error en facturación o precio",              "Método",        "Facturación"),
 ("Cliente sin cupo / cartera bloqueada",       "Método",        "Cartera"),
 ("Producto con calidad o rotación deficiente", "Material",      "Calidad"),
 ("Tráfico, cierre vial u orden público",       "Medio ambiente","Externo"),
 ("Clima adverso",                              "Medio ambiente","Externo"),
 ("Sin clasificar aún",                         "Por definir",   "Por definir"),
]
ESTADOS = [
 ("Sin gestionar", "NO"), ("En gestión", "NO"),
 ("Esperando a la transportadora", "NO"), ("Esperando al cliente", "NO"),
 ("Resuelta", "SÍ"), ("Anulada", "SÍ"),
]
PUNTOS = [  # donde ocurrio
 "En ruta / entrega al cliente", "Recepción de proveedor", "Almacenamiento",
 "Alistamiento (picking)", "Empaque", "Cargue del vehículo",
 "Despacho y coordinación", "Facturación y documentos", "Bodega de devoluciones",
 "Patio / zona de maniobras", "Oficina / administrativo", "Otro",
]
ORIGENES = ["En ruta", "Interna"]
TRANSP = ["Transportadora A", "Transportadora B", "Transportadora C", "Flota propia"]
RESPON = ["Coordinador de logística", "Jefe de bodega", "Analista de transporte",
          "Servicio al cliente", "Comercial", "Facturación", "Cartera", "Calidad",
          "Jefe de operaciones", "Seguridad y salud"]

title(cf, 1, "A", "T", "CONFIG · catálogos y reglas de negocio")
cf["A2"] = ("Aquí se cambia el comportamiento de toda la matriz sin tocar una sola fórmula. "
            "Agregue filas hacia abajo: las listas desplegables crecen solas.")
cf["A2"].font = f_note; cf.merge_cells("A2:T2")

CFG_HDR = [("A","TIPO DE NOVEDAD"),("B","ÁMBITO"),("C","GRAVEDAD"),("D","SLA (días hábiles)"),
           ("E","¿AFECTA LA ENTREGA?"),
           ("G","CAUSA RAÍZ"),("H","FAMILIA (6M)"),("I","ÁREA RESPONSABLE"),
           ("K","ESTADO"),("L","¿CIERRA EL CASO?"),
           ("N","PUNTO DE OCURRENCIA"),("P","ORIGEN"),("R","TRANSPORTADORA"),("T","RESPONSABLE")]
for col, tx in CFG_HDR:
    put(cf, f"{col}3", tx, font=f_hdr, fill=AMBER, al=CEN)
cf.row_dimensions[3].height = 30

def col_write(ws, col, row0, vals, fmt=None, al=None):
    for i, v in enumerate(vals):
        put(ws, f"{col}{row0+i}", v, fill=EDIT, fmt=fmt, al=al or LEF, editable=True)

col_write(cf,"A",4,[t[0] for t in TIPOS]); col_write(cf,"B",4,[t[1] for t in TIPOS], al=CEN)
col_write(cf,"C",4,[t[2] for t in TIPOS], al=CEN); col_write(cf,"D",4,[t[3] for t in TIPOS], NUM, CEN)
col_write(cf,"E",4,[t[4] for t in TIPOS], al=CEN)
col_write(cf,"G",4,[c[0] for c in CAUSAS]); col_write(cf,"H",4,[c[1] for c in CAUSAS], al=CEN)
col_write(cf,"I",4,[c[2] for c in CAUSAS], al=CEN)
col_write(cf,"K",4,[e[0] for e in ESTADOS]); col_write(cf,"L",4,[e[1] for e in ESTADOS], al=CEN)
col_write(cf,"N",4,PUNTOS); col_write(cf,"P",4,ORIGENES)
col_write(cf,"R",4,TRANSP); col_write(cf,"T",4,RESPON)

widths(cf, {"A":42,"B":11,"C":11,"D":15,"E":18,"F":2,"G":40,"H":16,"I":16,"J":2,
            "K":28,"L":16,"M":2,"N":28,"O":2,"P":12,"Q":2,"R":24,"S":2,"T":26})
for r in range(4, CFG1+1): cf.row_dimensions[r].height = 16
cf.freeze_panes = "A4"

BAND_A, BAND_B = INK2, "FF475569"

def build_grid(ws, cols, r0, r1, band_row=2, hdr_row=3):
    """cols: lista de (letra, encabezado, 'M'|'C', ancho, formato, alineacion)"""
    for col, tx, kind, w, fmt, al in cols:
        put(ws, f"{col}{hdr_row}", tx, font=f_hdr, fill=(AMBER if kind == "M" else BLUE), al=CEN)
        ws.column_dimensions[col].width = w
    ws.row_dimensions[hdr_row].height = 34
    for r in range(r0, r1 + 1):
        ws.row_dimensions[r].height = 16
        for col, tx, kind, w, fmt, al in cols:
            c = ws[f"{col}{r}"]
            c.font = f_base; c.border = BOX; c.number_format = fmt; c.alignment = al
            if kind == "M":
                c.fill = fl(EDIT); c.protection = Protection(locked=False)
            else:
                c.fill = fl(CALC)

# =========================================================================
# ENVIOS  -  base de despachos
# =========================================================================
ev = sheet("ENVIOS", BLUE)
title(ev, 1, "A", "P", "ENVÍOS · base de despachos")

ENV_COLS = [
 ("A","Nº Guía / Remisión",       "M", 18, "General", CEN),
 ("B","Fecha despacho",           "M", 13, FECHA,     CEN),
 ("C","Cliente",                  "M", 32, "General", LEF),
 ("D","Ciudad destino",           "M", 18, "General", LEF),
 ("E","Transportadora",           "M", 20, "General", LEF),
 ("F","Conductor",                "M", 22, "General", LEF),
 ("G","Placa",                    "M", 10, "General", CEN),
 ("H","Unidades enviadas",        "M", 13, NUM,       CEN),
 ("I","Valor del envío",          "M", 15, MONEY,     RIG),
 ("J","Fecha promesa de entrega", "M", 15, FECHA,     CEN),
 ("K","Fecha de entrega real",    "M", 15, FECHA,     CEN),
 ("L","Días en ruta",             "C", 11, NUM,       CEN),
 ("M","¿Llegó a tiempo?",         "C", 13, "General", CEN),
 ("N","Novedades",                "C", 11, NUM,       CEN),
 ("O","¿Llegó completa?",         "C", 13, "General", CEN),
 ("P","OTIF",                     "C", 11, "General", CEN),
]
banner(ev, 2, "A", "J", "① SE DIGITA AL DESPACHAR  ·  pegue o escriba aquí", BAND_A)
banner(ev, 2, "K", "K", "② AL ENTREGAR", BAND_B)
banner(ev, 2, "L", "P", "③ SE CALCULA SOLO  ·  no escriba en esta zona", BAND_A)
build_grid(ev, ENV_COLS, ENV0, ENV1)

FENV = {
 "L": '=IF(OR($A{r}="",$B{r}=""),"",IF($K{r}<>"",$K{r}-$B{r},TODAY()-$B{r}))',
 "M": '=IF(OR($A{r}="",$J{r}=""),"",IF($K{r}="",IF(TODAY()>$J{r},"Atrasado","En ruta"),IF($K{r}<=$J{r},"Sí","No")))',
 "N": '=IF($A{r}="","",COUNTIFS({nC},$A{r}))',
 "O": '=IF($A{r}="","",IF(COUNTIFS({nC},$A{r},{nM},"SÍ")>0,"No","Sí"))',
 "P": '=IF(OR($A{r}="",$K{r}=""),"",IF(AND($M{r}="Sí",$O{r}="Sí"),"OTIF","Falló"))',
}
for r in range(ENV0, ENV1 + 1):
    for col, f in FENV.items():
        ev[f"{col}{r}"] = f.format(r=r, nC=N("D"), nM=N("N"))
ev.freeze_panes = "C4"
ev.auto_filter.ref = f"A3:P{ENV1}"

# =========================================================================
# NOVEDADES  -  la matriz (en ruta + internas)
# =========================================================================
nv = sheet("NOVEDADES", AMBER)
title(nv, 1, "A", "AB", "MATRIZ DE NOVEDADES · logística y transporte")

NOV_COLS = [
 ("A","ID",                    "C", 10, "General", CEN),
 ("B","Fecha de la novedad",   "M", 14, FECHA,     CEN),
 ("C","Origen",                "M", 12, "General", CEN),
 ("D","Nº Guía / Remisión",    "M", 16, "General", CEN),
 ("E","Validación",            "C", 16, "General", CEN),
 ("F","Cliente",               "C", 28, "General", LEF),
 ("G","Ciudad destino",        "C", 16, "General", LEF),
 ("H","Transportadora",        "C", 18, "General", LEF),
 ("I","Conductor",             "C", 20, "General", LEF),
 ("J","Placa",                 "C", 10, "General", CEN),
 ("K","Fecha despacho",        "C", 13, FECHA,     CEN),
 ("L","Tipo de novedad",       "M", 34, "General", LEF),
 ("M","Gravedad",              "C", 11, "General", CEN),
 ("N","¿Afecta la entrega?",   "C", 13, "General", CEN),
 ("O","Punto de ocurrencia",   "M", 24, "General", LEF),
 ("P","Causa raíz",            "M", 34, "General", LEF),
 ("Q","Familia (6M)",          "C", 15, "General", CEN),
 ("R","Área responsable",      "C", 15, "General", CEN),
 ("S","Unidades afectadas",    "M", 13, NUM,       CEN),
 ("T","Valor afectado",        "M", 15, MONEY,     RIG),
 ("U","Estado",                "M", 26, "General", LEF),
 ("V","Responsable",           "M", 24, "General", LEF),
 ("W","Fecha límite",          "C", 13, FECHA,     CEN),
 ("X","Fecha de solución",     "M", 14, FECHA,     CEN),
 ("Y","Días abiertos",         "C", 11, NUM,       CEN),
 ("Z","Estado SLA",            "C", 18, "General", CEN),
 ("AA","Qué se hizo",          "M", 38, "General", LEF),
 ("AB","Notas / soporte",      "M", 32, "General", LEF),
]
banner(nv, 2, "A", "K", "① IDENTIFICAR  ·  fecha y origen siempre; el Nº de guía solo si la novedad fue en ruta", BAND_A)
banner(nv, 2, "L", "R", "② CLASIFICAR  ·  qué pasó, dónde y por qué", BAND_B)
banner(nv, 2, "S", "T", "③ IMPACTO", BAND_A)
banner(nv, 2, "U", "Z", "④ GESTIONAR Y CERRAR", BAND_B)
banner(nv, 2, "AA", "AB", "⑤ CONSTANCIA", BAND_A)
build_grid(nv, NOV_COLS, NOV0, NOV1)

BUSCA = 'IFERROR(INDEX({rng},MATCH($D{r},{eA},0)),"—")'
FNOV = {
 "A": '=IF($B{r}="","","N-"&TEXT(ROW()-3,"0000"))',
 "E": ('=IF($C{r}="","",IF($D{r}="",IF($C{r}="Interna","Sin guía (interna)","FALTA GUÍA"),'
       'IF(COUNTIFS({eA},$D{r})=0,"NO EXISTE",IF(COUNTIFS({eA},$D{r})>1,"DUPLICADA","OK"))))'),
 "F": '=IF($D{r}="","",' + BUSCA.format(rng=E("C"), eA=E("A"), r="{r}") + ')',
 "G": '=IF($D{r}="","",' + BUSCA.format(rng=E("D"), eA=E("A"), r="{r}") + ')',
 "H": '=IF($D{r}="","",' + BUSCA.format(rng=E("E"), eA=E("A"), r="{r}") + ')',
 "I": '=IF($D{r}="","",' + BUSCA.format(rng=E("F"), eA=E("A"), r="{r}") + ')',
 "J": '=IF($D{r}="","",' + BUSCA.format(rng=E("G"), eA=E("A"), r="{r}") + ')',
 "K": '=IF($D{r}="","",IFERROR(INDEX({eB},MATCH($D{r},{eA},0)),""))',
 "M": '=IF($L{r}="","",IFERROR(INDEX({cC},MATCH($L{r},{cA},0)),"Media"))',
 "N": '=IF($L{r}="","",IF($C{r}="Interna","NO",IFERROR(INDEX({cE},MATCH($L{r},{cA},0)),"NO")))',
 "Q": '=IF($P{r}="","",IFERROR(INDEX({cH},MATCH($P{r},{cG},0)),"Por definir"))',
 "R": '=IF($P{r}="","",IFERROR(INDEX({cI},MATCH($P{r},{cG},0)),"Por definir"))',
 "W": '=IF(OR($B{r}="",$L{r}=""),"",WORKDAY($B{r},IFERROR(INDEX({cD},MATCH($L{r},{cA},0)),3)))',
 "Y": '=IF($B{r}="","",IF($X{r}<>"",$X{r}-$B{r},TODAY()-$B{r}))',
 "Z": ('=IF($B{r}="","",IF(IFERROR(INDEX({cL},MATCH($U{r},{cK},0)),"NO")="SÍ",'
       'IF(OR($X{r}="",$W{r}=""),"Resuelta",IF($X{r}>$W{r},"Resuelta tarde","Resuelta a tiempo")),'
       'IF($W{r}="","Sin clasificar",IF(TODAY()>$W{r},"Vencida",IF(TODAY()>=$W{r}-1,"Por vencer","En plazo")))))'),
}
ARG = dict(eA=E("A"), eB=E("B"), cA=C("A"), cC=C("C"), cD=C("D"), cE=C("E"),
           cG=C("G"), cH=C("H"), cI=C("I"), cK=C("K"), cL=C("L"))
for r in range(NOV0, NOV1 + 1):
    for col, f in FNOV.items():
        nv[f"{col}{r}"] = f.format(r=r, **ARG)
nv.freeze_panes = "E4"
nv.auto_filter.ref = f"A3:AB{NOV1}"

# =========================================================================
# TABLERO
# =========================================================================
tb = sheet("TABLERO", INK)
widths(tb, {"A":2,"B":24,"C":15,"D":13,"E":13,"F":13,"G":13,"H":13,"I":13,
            "J":13,"K":15,"L":13,"M":13,"N":2})

title(tb, 2, "B", "M", "TABLERO DE NOVEDADES · logística y transporte")
tb["B3"] = ("Todo se filtra por el periodo de abajo. Novedades por su fecha de registro; envíos por su fecha de despacho.")
tb["B3"].font = f_note; tb.merge_cells("B3:M3")

put(tb, "B4", "PERIODO", font=f_hdr, fill=INK2, al=CEN); tb.merge_cells("B4:C4")
put(tb, "D4", "Desde:", font=f_bold, al=RIG, box=False)
put(tb, "E4", datetime.date(2026,1,1), font=Font(name=FN, size=11, bold=True, color=INK),
    fill=EDIT, fmt=FECHA, al=CEN, editable=True)
put(tb, "F4", "Hasta:", font=f_bold, al=RIG, box=False)
put(tb, "G4", datetime.date(2026,12,31), font=Font(name=FN, size=11, bold=True, color=INK),
    fill=EDIT, fmt=FECHA, al=CEN, editable=True)
put(tb, "H4", "◄ cambie estas dos fechas y todo el tablero se recalcula", font=f_note, al=LEF, box=False)
tb.merge_cells("H4:M4"); tb.row_dimensions[4].height = 22

PN = f'{N("B")},">="&$E$4,{N("B")},"<="&$G$4'
PE = f'{E("B")},">="&$E$4,{E("B")},"<="&$G$4'
ABIERTAS = lambda extra="": "+".join(
    f'COUNTIFS({N("Z")},"{s}",{PN}{extra})' for s in ["En plazo","Por vencer","Vencida","Sin clasificar"])
ENTREGADOS = f'(COUNTIFS({E("P")},"OTIF",{PE})+COUNTIFS({E("P")},"Falló",{PE}))'

def kpi_row(row, label, cards):
    put(tb, f"B{row}", label, font=Font(name=FN, size=10, bold=True, color=WHITE), fill=INK2, al=CEN)
    tb.merge_cells(start_row=row, start_column=2, end_row=row+1, end_column=3)
    for c0, c1, lbl, frm, fmt in cards:
        h = tb.cell(row=row, column=ci(c0), value=lbl)
        h.font = f_kpil; h.fill = fl(CARD); h.alignment = CEN; h.border = BOX
        tb.merge_cells(start_row=row, start_column=ci(c0), end_row=row, end_column=ci(c1))
        v = tb.cell(row=row+1, column=ci(c0), value=frm)
        v.font = f_kpi; v.fill = fl(CARD); v.alignment = CEN; v.border = BOX; v.number_format = fmt
        tb.merge_cells(start_row=row+1, start_column=ci(c0), end_row=row+1, end_column=ci(c1))
    tb.row_dimensions[row].height = 20; tb.row_dimensions[row+1].height = 34

kpi_row(6, "LAS ENTREGAS", [
 ("D","E","OTIF (a tiempo y completo)", f'=IFERROR(COUNTIFS({E("P")},"OTIF",{PE})/{ENTREGADOS},"—")', PCT),
 ("F","G","ENTREGAS A TIEMPO",          f'=IFERROR(COUNTIFS({E("M")},"Sí",{PE})/{ENTREGADOS},"—")', PCT),
 ("H","I","TASA DE NOVEDADES",          f'=IFERROR(COUNTIFS({E("N")},">0",{PE})/COUNTIFS({PE}),"—")', PCT),
 ("J","K","VALOR AFECTADO",             f'=SUMIFS({N("T")},{PN})', MONEY),
 ("L","M","ENVÍOS DEL PERIODO",         f'=COUNTIFS({PE})', NUM),
])
kpi_row(9, "LA GESTIÓN", [
 ("D","E","NOVEDADES",            f'=COUNTIFS({PN})', NUM),
 ("F","G","ABIERTAS",             "=" + ABIERTAS(), NUM),
 ("H","I","VENCIDAS (SLA roto)",  f'=COUNTIFS({N("Z")},"Vencida",{PN})', NUM),
 ("J","K","DÍAS PROM. SOLUCIÓN",  f'=IFERROR(ROUND(AVERAGEIFS({N("Y")},{PN}),1),0)', DEC),
 ("L","M","CUMPLIMIENTO DE SLA",  f'=IFERROR(COUNTIFS({N("Z")},"Resuelta a tiempo",{PN})/COUNTIFS({N("Z")},"Resuelta*",{PN}),"—")', PCT),
])
kpi_row(12, "DÓNDE NACEN", [
 ("D","E","EN RUTA (transporte)", f'=COUNTIFS({N("C")},"En ruta",{PN})', NUM),
 ("F","G","INTERNAS (la empresa)",f'=COUNTIFS({N("C")},"Interna",{PN})', NUM),
 ("H","I","% INTERNAS",           f'=IFERROR(COUNTIFS({N("C")},"Interna",{PN})/COUNTIFS({PN}),"—")', PCT),
 ("J","K","VALOR DE LAS INTERNAS",f'=SUMIFS({N("T")},{N("C")},"Interna",{PN})', MONEY),
 ("L","M","PUNTO INTERNO MÁS FRECUENTE",
                                  '=IF(MAX($D$87:$D$97)=0,"—",IFERROR(INDEX($B$87:$B$97,'
                                  'MATCH(MAX($D$87:$D$97),$D$87:$D$97,0)),"—"))', "General"),
])
tb["L13"].font = Font(name=FN, size=11, bold=True, color=INK)

def thead(row, cols):
    for col, tx in cols:
        put(tb, f"{col}{row}", tx, font=f_hdr, fill=BLUE, al=CEN)
    tb.row_dimensions[row].height = 32

def cell(coord, val, fmt="General", al=None, bold=False):
    return put(tb, coord, val, font=(f_bold if bold else f_base),
               fill=(CARD if bold else CALC), fmt=fmt, al=al or CEN)

def name_cell(row, formula, bold=False):
    c = put(tb, f"B{row}", formula, font=(f_bold if bold else f_base),
            fill=(CARD if bold else CALC), al=LEF)
    put(tb, f"C{row}", None, font=f_base, fill=(CARD if bold else CALC), al=LEF)
    tb.merge_cells(start_row=row, start_column=2, end_row=row, end_column=3)
    return c

def relleno(row, cols, bold=False):
    for col in cols: cell(f"{col}{row}", None, bold=bold)

# ---- 1. SCORECARD DE TRANSPORTADORAS ----
seccion(tb, 15, "B", "M", "1 · SCORECARD DE TRANSPORTADORAS")
tb["B16"] = ("Solo cuenta las novedades EN RUTA: las internas no son culpa del transportador.   "
             "Nota A = 90 puntos o más · B = 80 a 89 · C = 70 a 79 · D = menos de 70.   "
             "Puntaje = OTIF ×60 + (1 − tasa) ×25 + (1 − vencidas/novedades) ×15.")
tb["B16"].font = f_note; tb.merge_cells("B16:M16")
thead(17, [("B","Transportadora"),("D","Envíos"),("E","OTIF"),("F","Novedades"),("G","Tasa"),
           ("H","Abiertas"),("I","Vencidas"),("J","Días prom."),("K","Valor afectado"),
           ("L","Puntaje"),("M","Nota")])
tb["C17"].fill = fl(BLUE); tb["C17"].border = BOX; tb.merge_cells("B17:C17")
for r in range(18, 28):
    lr = r - 14
    name_cell(r, f'=IF(CONFIG!$R{lr}="","",CONFIG!$R{lr})')
    g = f'{N("H")},$B{r}'; e = f'{E("E")},$B{r}'
    cell(f"D{r}", f'=IF($B{r}="","",COUNTIFS({e},{PE}))', NUM)
    cell(f"E{r}", f'=IF($B{r}="","",IFERROR(COUNTIFS({e},{E("P")},"OTIF",{PE})'
                  f'/(COUNTIFS({e},{E("P")},"OTIF",{PE})+COUNTIFS({e},{E("P")},"Falló",{PE})),"—"))', PCT1)
    cell(f"F{r}", f'=IF($B{r}="","",COUNTIFS({g},{PN}))', NUM)
    cell(f"G{r}", f'=IF($B{r}="","",IFERROR(COUNTIFS({e},{E("N")},">0",{PE})/$D{r},"—"))', PCT1)
    cell(f"H{r}", f'=IF($B{r}="","",{ABIERTAS(f",{g}")})', NUM)
    cell(f"I{r}", f'=IF($B{r}="","",COUNTIFS({g},{N("Z")},"Vencida",{PN}))', NUM)
    cell(f"J{r}", f'=IF($B{r}="","",IFERROR(ROUND(AVERAGEIFS({N("Y")},{g},{PN}),1),0))', DEC)
    cell(f"K{r}", f'=IF($B{r}="","",SUMIFS({N("T")},{g},{PN}))', MONEY)
    cell(f"L{r}", f'=IF(OR($B{r}="",$D{r}=0,NOT(ISNUMBER($E{r}))),"—",'
                  f'ROUND($E{r}*60+(1-N($G{r}))*25+IF($F{r}=0,15,(1-$I{r}/$F{r})*15),0))', NUM)
    cell(f"M{r}", f'=IF(NOT(ISNUMBER($L{r})),"—",IF($L{r}>=90,"A",IF($L{r}>=80,"B",IF($L{r}>=70,"C","D"))))')
name_cell(28, '="TOTAL"', bold=True)
for col in "DFHI": cell(f"{col}28", f"=SUM(${col}$18:${col}$27)", NUM, bold=True)
cell("E28", f'=IFERROR(COUNTIFS({E("P")},"OTIF",{PE})/{ENTREGADOS},"—")', PCT1, bold=True)
cell("G28", f'=IFERROR(COUNTIFS({E("N")},">0",{PE})/COUNTIFS({PE}),"—")', PCT1, bold=True)
cell("J28", f'=IFERROR(ROUND(AVERAGEIFS({N("Y")},{N("C")},"En ruta",{PN}),1),0)', DEC, bold=True)
cell("K28", "=SUM($K$18:$K$27)", MONEY, bold=True)
relleno(28, "LM", bold=True)

# ---- 2. PARETO DE CAUSA RAIZ ----
seccion(tb, 30, "B", "M", "2 · PARETO DE CAUSA RAÍZ — dónde atacar primero")
tb["B31"] = ("Regla 80/20: las causas que aparecen hasta llegar a 80% en la columna «% acumulado» "
             "son las que explican casi todas sus novedades. Empiece por ahí. Incluye en ruta e internas.")
tb["B31"].font = f_note; tb.merge_cells("B31:M31")
thead(32, [("B","Causa raíz"),("D","Casos"),("E","% de las novedades"),("F","% acumulado"),
           ("G","Valor afectado"),("H","Familia (6M)"),("I","Área responsable")])
tb["C32"].fill = fl(BLUE); tb["C32"].border = BOX; tb.merge_cells("B32:C32")
for col in "JKLM": put(tb, f"{col}32", None, font=f_hdr, fill=BLUE, al=CEN)
HELP = "CONFIG!$V$4:$V$33"; CAUS = "CONFIG!$G$4:$G$33"
for r in range(33, 45):
    k = r - 32
    name_cell(r, f'=IFERROR(INDEX({CAUS},MATCH(LARGE({HELP},{k}),{HELP},0)),"")')
    cell(f"D{r}", f'=IF($B{r}="","",ROUNDDOWN(LARGE({HELP},{k}),0))', NUM)
    cell(f"E{r}", f'=IF($B{r}="","",IFERROR($D{r}/$D$45,0))', PCT1)
    cell(f"F{r}", f'=IF($B{r}="","",IFERROR(SUM($D$33:$D{r})/$D$45,0))', PCT1)
    cell(f"G{r}", f'=IF($B{r}="","",SUMIFS({N("T")},{N("P")},$B{r},{PN}))', MONEY)
    cell(f"H{r}", f'=IF($B{r}="","",IFERROR(INDEX({C("H")},MATCH($B{r},{C("G")},0)),""))')
    cell(f"I{r}", f'=IF($B{r}="","",IFERROR(INDEX({C("I")},MATCH($B{r},{C("G")},0)),""))')
    relleno(r, "JKLM")
name_cell(45, '="TOTAL de novedades del periodo"', bold=True)
cell("D45", f'=COUNTIFS({PN})', NUM, bold=True)
cell("E45", '=IF($D$45=0,0,1)', PCT1, bold=True); cell("F45", "", bold=True)
cell("G45", f'=SUMIFS({N("T")},{PN})', MONEY, bold=True)
relleno(45, "HIJKLM", bold=True)

# ---- 3. NOVEDADES POR TIPO ----
seccion(tb, 47, "B", "M", "3 · NOVEDADES POR TIPO — qué está pasando")
thead(48, [("B","Tipo de novedad"),("D","Casos"),("E","% del total"),("F","Valor afectado"),
           ("G","Ámbito"),("H","Gravedad"),("I","Abiertas"),("J","Vencidas"),("K","Días prom.")])
tb["C48"].fill = fl(BLUE); tb["C48"].border = BOX; tb.merge_cells("B48:C48")
for col in "LM": put(tb, f"{col}48", None, font=f_hdr, fill=BLUE, al=CEN)
for r in range(49, 81):
    lr = r - 45
    name_cell(r, f'=IF(CONFIG!$A{lr}="","",CONFIG!$A{lr})')
    t = f'{N("L")},$B{r}'
    cell(f"D{r}", f'=IF($B{r}="","",COUNTIFS({t},{PN}))', NUM)
    cell(f"E{r}", f'=IF($B{r}="","",IFERROR($D{r}/$D$81,0))', PCT1)
    cell(f"F{r}", f'=IF($B{r}="","",SUMIFS({N("T")},{t},{PN}))', MONEY)
    cell(f"G{r}", f'=IF($B{r}="","",IFERROR(INDEX({C("B")},MATCH($B{r},{C("A")},0)),""))')
    cell(f"H{r}", f'=IF($B{r}="","",IFERROR(INDEX({C("C")},MATCH($B{r},{C("A")},0)),""))')
    cell(f"I{r}", f'=IF($B{r}="","",{ABIERTAS(f",{t}")})', NUM)
    cell(f"J{r}", f'=IF($B{r}="","",COUNTIFS({t},{N("Z")},"Vencida",{PN}))', NUM)
    cell(f"K{r}", f'=IF($B{r}="","",IFERROR(ROUND(AVERAGEIFS({N("Y")},{t},{PN}),1),0))', DEC)
    relleno(r, "LM")
name_cell(81, '="TOTAL"', bold=True)
for col in "DIJ": cell(f"{col}81", f"=SUM(${col}$49:${col}$80)", NUM, bold=True)
cell("E81", '=IF($D$81=0,0,1)', PCT1, bold=True)
cell("F81", "=SUM($F$49:$F$80)", MONEY, bold=True)
cell("K81", f'=IFERROR(ROUND(AVERAGEIFS({N("Y")},{PN}),1),0)', DEC, bold=True)
relleno(81, "GHLM", bold=True)

# ---- 4. DONDE OCURREN LAS NOVEDADES ----
seccion(tb, 83, "B", "M", "4 · PUNTO DE OCURRENCIA — en qué parte de la operación se rompe")
tb["B84"] = ("Aquí se ve si el problema nace en la carretera o adentro: bodega, alistamiento, "
             "cargue, facturación. Es el mapa de la casa propia.")
tb["B84"].font = f_note; tb.merge_cells("B84:M84")
thead(85, [("B","Punto de ocurrencia"),("D","Casos"),("E","% del total"),("F","Valor afectado"),
           ("G","Abiertas"),("H","Vencidas"),("I","Días prom.")])
tb["C85"].fill = fl(BLUE); tb["C85"].border = BOX; tb.merge_cells("B85:C85")
for col in "JKLM": put(tb, f"{col}85", None, font=f_hdr, fill=BLUE, al=CEN)
for r in range(86, 98):
    lr = r - 82
    name_cell(r, f'=IF(CONFIG!$N{lr}="","",CONFIG!$N{lr})')
    q = f'{N("O")},$B{r}'
    cell(f"D{r}", f'=IF($B{r}="","",COUNTIFS({q},{PN}))', NUM)
    cell(f"E{r}", f'=IF($B{r}="","",IFERROR($D{r}/$D$98,0))', PCT1)
    cell(f"F{r}", f'=IF($B{r}="","",SUMIFS({N("T")},{q},{PN}))', MONEY)
    cell(f"G{r}", f'=IF($B{r}="","",{ABIERTAS(f",{q}")})', NUM)
    cell(f"H{r}", f'=IF($B{r}="","",COUNTIFS({q},{N("Z")},"Vencida",{PN}))', NUM)
    cell(f"I{r}", f'=IF($B{r}="","",IFERROR(ROUND(AVERAGEIFS({N("Y")},{q},{PN}),1),0))', DEC)
    relleno(r, "JKLM")
name_cell(98, '="TOTAL con punto asignado"', bold=True)
for col in "DGH": cell(f"{col}98", f"=SUM(${col}$86:${col}$97)", NUM, bold=True)
cell("E98", '=IF($D$98=0,0,1)', PCT1, bold=True)
cell("F98", "=SUM($F$86:$F$97)", MONEY, bold=True)
relleno(98, "IJKLM", bold=True)

# ---- 5. ESTADO DE LA GESTION  +  FAMILIA 6M ----
seccion(tb, 100, "B", "M", "5 · ESTADO DE LA GESTIÓN  y  FAMILIA DE LA CAUSA (6M de Ishikawa)")
thead(101, [("B","Estado"),("D","Casos"),("E","% del total"),
            ("G","Familia (6M)"),("I","Casos"),("J","% del total"),("K","Valor afectado")])
tb["C101"].fill = fl(BLUE); tb["C101"].border = BOX; tb.merge_cells("B101:C101")
tb["H101"].fill = fl(BLUE); tb["H101"].border = BOX; tb.merge_cells("G101:H101")
for col in "FLM": put(tb, f"{col}101", None, font=f_hdr, fill=BLUE, al=CEN)
FAMILIAS = ["Método","Material","Medición","Mano de obra","Máquina","Medio ambiente","Externo","Por definir"]
for r in range(102, 110):
    i = r - 102
    if i < 6:
        lr = r - 98
        name_cell(r, f'=IF(CONFIG!$K{lr}="","",CONFIG!$K{lr})')
        cell(f"D{r}", f'=IF($B{r}="","",COUNTIFS({N("U")},$B{r},{PN}))', NUM)
        cell(f"E{r}", f'=IF($B{r}="","",IFERROR($D{r}/$D$110,0))', PCT1)
    else:
        name_cell(r, None); cell(f"D{r}", None); cell(f"E{r}", None)
    put(tb, f"F{r}", None, fill=CALC, al=CEN)
    put(tb, f"G{r}", FAMILIAS[i], fill=CALC, al=LEF)
    put(tb, f"H{r}", None, fill=CALC, al=LEF); tb.merge_cells(f"G{r}:H{r}")
    cell(f"I{r}", f'=COUNTIFS({N("Q")},$G{r},{PN})', NUM)
    cell(f"J{r}", f'=IFERROR($I{r}/$I$110,0)', PCT1)
    cell(f"K{r}", f'=SUMIFS({N("T")},{N("Q")},$G{r},{PN})', MONEY)
    relleno(r, "LM")
name_cell(110, '="TOTAL"', bold=True)
cell("D110", "=SUM($D$102:$D$107)", NUM, bold=True); cell("E110", '=IF($D$110=0,0,1)', PCT1, bold=True)
put(tb, "F110", None, fill=CARD, al=CEN)
put(tb, "G110", "TOTAL", font=f_bold, fill=CARD, al=LEF); put(tb, "H110", None, fill=CARD)
tb.merge_cells("G110:H110")
cell("I110", "=SUM($I$102:$I$109)", NUM, bold=True); cell("J110", '=IF($I$110=0,0,1)', PCT1, bold=True)
cell("K110", "=SUM($K$102:$K$109)", MONEY, bold=True)
relleno(110, "LM", bold=True)

# ---- 6. BUSCADOR DE GUIA ----
seccion(tb, 112, "B", "M", "6 · BUSCADOR — la ficha completa de un envío")
put(tb, "B113", "Escriba el Nº de guía →", font=f_bold, fill=CARD, al=LEF)
put(tb, "C113", None, fill=CARD); tb.merge_cells("B113:C113")
put(tb, "D113", None, font=Font(name=FN, size=12, bold=True, color=INK), fill=EDIT, al=CEN, editable=True)
put(tb, "E113", None, fill=EDIT, editable=True); tb.merge_cells("D113:E113")
put(tb, "F113", "◄ la ficha de abajo se llena sola (solo aplica a novedades en ruta)", font=f_note, al=LEF, box=False)
tb.merge_cells("F113:M113"); tb.row_dimensions[113].height = 22

LK = lambda rng: f'IFERROR(INDEX({rng},MATCH($D$113,{E("A")},0)),"—")'
FICHA = [
 ("Cliente",               f'=IF($D$113="","—",{LK(E("C"))})', "General"),
 ("Ciudad destino",        f'=IF($D$113="","—",{LK(E("D"))})', "General"),
 ("Transportadora",        f'=IF($D$113="","—",{LK(E("E"))})', "General"),
 ("Conductor",             f'=IF($D$113="","—",{LK(E("F"))})', "General"),
 ("Placa",                 f'=IF($D$113="","—",{LK(E("G"))})', "General"),
 ("Fecha despacho",        f'=IF($D$113="","—",{LK(E("B"))})', FECHA),
 ("Fecha promesa",         f'=IF($D$113="","—",{LK(E("J"))})', FECHA),
 ("Fecha entrega real",    f'=IF($D$113="","—",{LK(E("K"))})', FECHA),
 ("¿Llegó a tiempo?",      f'=IF($D$113="","—",{LK(E("M"))})', "General"),
 ("¿Llegó completa?",      f'=IF($D$113="","—",{LK(E("O"))})', "General"),
 ("OTIF",                  f'=IF($D$113="","—",{LK(E("P"))})', "General"),
 ("Novedades registradas", f'=IF($D$113="","—",COUNTIFS({N("D")},$D$113))', NUM),
 ("Valor afectado",        f'=IF($D$113="","—",SUMIFS({N("T")},{N("D")},$D$113))', MONEY),
 ("Última novedad",        f'=IF($D$113="","—",IFERROR(LOOKUP(2,1/({N("D")}=$D$113),{N("L")}),"—"))', "General"),
 ("Estado de esa novedad", f'=IF($D$113="","—",IFERROR(LOOKUP(2,1/({N("D")}=$D$113),{N("U")}),"—"))', "General"),
 ("Estado SLA",            f'=IF($D$113="","—",IFERROR(LOOKUP(2,1/({N("D")}=$D$113),{N("Z")}),"—"))', "General"),
]
for i, (lbl, frm, fmt) in enumerate(FICHA):
    r = 115 + i
    put(tb, f"B{r}", lbl, font=f_base, fill=CARD, al=LEF)
    put(tb, f"C{r}", None, fill=CARD); tb.merge_cells(f"B{r}:C{r}")
    put(tb, f"D{r}", frm, font=f_bold, fill=CALC, fmt=fmt, al=LEF)
    for col in "EF": put(tb, f"{col}{r}", None, fill=CALC)
    tb.merge_cells(f"D{r}:F{r}")
    tb.row_dimensions[r].height = 16
tb.freeze_panes = "B5"

# ---- columna auxiliar del Pareto, en CONFIG ----
put(cf, "V3", "⚙ CÁLCULO DEL TABLERO — no borrar", font=f_hdr, fill=INK2, al=CEN)
cf.column_dimensions["U"].width = 2; cf.column_dimensions["V"].width = 30
for r in range(4, 34):
    put(cf, f"V{r}", f'=IF($G{r}="","",COUNTIFS({N("P")},$G{r},{N("B")},">="&TABLERO!$E$4,'
                     f'{N("B")},"<="&TABLERO!$G$4)+ROW()/100000)',
        font=f_base, fill=CALC, fmt="0.00000", al=CEN)

# =========================================================================
# INICIO
# =========================================================================
ini = sheet("INICIO", "FF16A34A")
widths(ini, {"A":2, "B":6, "C":148})
GUIA = [
 ("T", "", "MATRIZ DE NOVEDADES · LOGÍSTICA Y TRANSPORTE"),
 ("P", "", "Un solo archivo para registrar todo lo que sale mal —en la carretera y dentro de la empresa—, saber a quién cobrárselo y medir si la operación está mejorando."),
 ("H", "", "CÓMO SE USA — TRES PASOS"),
 ("S", "1", "ENVÍOS.  Cada despacho es una fila. Escriba guía, fecha, cliente, ciudad, transportadora, conductor, placa, unidades, valor y la FECHA PROMESA DE ENTREGA. Cuando llegue, escriba la fecha de entrega real. Con eso el archivo calcula solo si llegó a tiempo y si llegó completo."),
 ("S", "2", "NOVEDADES.  ¿Algo salió mal? Escriba la fecha, marque el ORIGEN y clasifique. Si fue en ruta, agregue el Nº de guía y el cliente, la ciudad, la transportadora, el conductor y la placa se traen solos."),
 ("S", "3", "TABLERO.  Ponga el periodo arriba y lea. Le dice su OTIF, qué transportadora rinde y cuál no, en qué punto de la operación se rompe y cuáles causas explican el 80% de sus problemas."),
 ("H", "", "LAS DOS CLASES DE NOVEDAD"),
 ("P", "", "EN RUTA: pasó con un envío ya despachado (cliente ausente, avería, retraso, rechazo). Lleva Nº de guía y se le carga a la transportadora."),
 ("P", "", "INTERNA: pasó dentro de la empresa, casi siempre antes de despachar (error de alistamiento, descuadre de inventario, demora en el cargue, falla de un equipo de bodega, accidente laboral). NO lleva guía: deje esa casilla vacía y la validación dirá «Sin guía (interna)», que es lo correcto."),
 ("P", "", "Las internas nunca entran al scorecard de transportadoras ni a la tasa de novedades por envío, porque no son culpa del transportador ni corresponden a una entrega. Sí entran al Pareto de causas, a las 6M y al punto de ocurrencia — que es donde usted mira su propia casa."),
 ("H", "", "LA REGLA DE COLORES"),
 ("P", "", "AMARILLO = usted lo escribe.        GRIS = se calcula solo, no lo toque.        Encabezado dorado = columna de captura.        Encabezado azul = columna calculada."),
 ("P", "", "Además, cada hoja tiene una banda oscura arriba que separa las zonas: lo que se digita, lo que se calcula y lo que es seguimiento."),
 ("H", "", "LOS NÚMEROS QUE IMPORTAN"),
 ("P", "", "OTIF (On Time In Full): de los envíos ya entregados, cuántos llegaron a tiempo Y completos. Es el estándar de la industria; una operación sana anda por encima del 95%."),
 ("P", "", "TASA DE NOVEDADES: de cada 100 envíos, cuántos tuvieron algún problema en ruta. Cuenta envíos afectados, no novedades, para que no se infle cuando un envío genera tres."),
 ("P", "", "% INTERNAS: qué parte de sus novedades nace adentro. Si es alto, el problema no es el transportador."),
 ("P", "", "CUMPLIMIENTO DE SLA: de las novedades ya resueltas, cuántas se resolvieron dentro del plazo que usted mismo definió por tipo."),
 ("P", "", "PUNTAJE Y NOTA POR TRANSPORTADORA: A, B, C o D. Es la hoja que se lleva a la reunión de negociación."),
 ("H", "", "CÓMO CAMBIAR LAS REGLAS SIN TOCAR FÓRMULAS"),
 ("P", "", "Todo vive en la hoja CONFIG: los tipos de novedad con su ámbito, su gravedad y su plazo en días hábiles; las causas raíz con su familia 6M y su área responsable; los estados y cuáles cierran el caso; los puntos de ocurrencia, las transportadoras y los responsables."),
 ("P", "", "Agregue filas hacia abajo y listo: las listas desplegables crecen solas y el tablero las recoge en el siguiente cálculo. Reemplace «Transportadora A, B, C» por los nombres reales antes de empezar."),
 ("H", "", "SOBRE LA CAUSA RAÍZ (LAS 6M)"),
 ("P", "", "Cada causa está clasificada en una de las seis familias del diagrama de Ishikawa: Método, Material, Medición, Mano de obra, Máquina y Medio ambiente (más Externo y Por definir). Sirve para ver si sus problemas son de proceso, de gente, de equipos o de afuera — y esa respuesta cambia qué se hace al respecto."),
 ("H", "", "DETALLES PRÁCTICOS"),
 ("P", "", "Las hojas están protegidas para no dañar las fórmulas, pero SIN contraseña: Revisar → Desproteger hoja y ya. Los plazos se cuentan en días hábiles (sin sábados ni domingos); si quiere descontar festivos, agregue una columna de fechas festivas en CONFIG y páselas como tercer argumento de DIA.LAB."),
 ("P", "", "Capacidad: 3.000 envíos y 1.500 novedades. Cuando se acerque al tope, guarde una copia con el nombre del periodo y borre solo las celdas amarillas."),
]
r = 2
for kind, num, txt in GUIA:
    if kind == "T":
        c = ini.cell(row=r, column=2, value=txt); c.font = f_title; c.fill = fl(INK)
        c.alignment = Alignment(horizontal="left", vertical="center", indent=1)
        ini.merge_cells(start_row=r, start_column=2, end_row=r, end_column=3)
        ini.row_dimensions[r].height = 40
    elif kind == "H":
        c = ini.cell(row=r, column=2, value=txt); c.font = f_sec; c.fill = fl(INK2)
        c.alignment = Alignment(horizontal="left", vertical="center", indent=1)
        ini.merge_cells(start_row=r, start_column=2, end_row=r, end_column=3)
        ini.row_dimensions[r].height = 24
    elif kind == "S":
        n = ini.cell(row=r, column=2, value=num)
        n.font = Font(name=FN, size=16, bold=True, color=WHITE); n.fill = fl(BLUE); n.alignment = CEN
        t = ini.cell(row=r, column=3, value=txt); t.font = f_base; t.fill = fl(CARD); t.alignment = LEFW
        ini.row_dimensions[r].height = 42
    else:
        ini.cell(row=r, column=2, value=None).fill = fl(WHITE)
        c = ini.cell(row=r, column=3, value=txt); c.font = f_base; c.alignment = LEFW
        ini.row_dimensions[r].height = 32
    r += 1

# =========================================================================
# NOMBRES, VALIDACION, FORMATO CONDICIONAL
# =========================================================================
DYN = lambda col: f"OFFSET(CONFIG!${col}$4,0,0,MAX(1,COUNTA(CONFIG!${col}$4:${col}$63)),1)"
for nm, col in [("TIPOS_NOVEDAD","A"), ("CAUSAS_RAIZ","G"), ("ESTADOS_NOVEDAD","K"),
                ("PUNTOS_OCURRENCIA","N"), ("ORIGENES","P"),
                ("TRANSPORTADORAS","R"), ("RESPONSABLES","T")]:
    wb.defined_names.add(DefinedName(nm, attr_text=DYN(col)))

def dv(ws, rng, warn=False, **kw):
    d = DataValidation(**kw); ws.add_data_validation(d); d.add(rng)
    if warn: d.errorStyle = "warning"
    return d

R_NOV = lambda c: f"{c}{NOV0}:{c}{NOV1}"
R_ENV = lambda c: f"{c}{ENV0}:{c}{ENV1}"
LISTA = dict(type="list", allow_blank=True, showErrorMessage=True)
dv(nv, R_NOV("C"), formula1="ORIGENES", errorTitle="Origen no válido",
   error="«En ruta» si pasó con un envío despachado; «Interna» si pasó dentro de la empresa.",
   promptTitle="Origen", prompt="En ruta = lleva Nº de guía.  Interna = deje la guía vacía.",
   showInputMessage=True, **LISTA)
dv(nv, R_NOV("L"), formula1="TIPOS_NOVEDAD", errorTitle="Tipo no válido",
   error="Elíjalo de la lista. Para agregar uno nuevo vaya a CONFIG, columna A.",
   promptTitle="Tipo de novedad", prompt="Define la gravedad y el plazo (SLA).", showInputMessage=True, **LISTA)
dv(nv, R_NOV("O"), formula1="PUNTOS_OCURRENCIA", errorTitle="Punto no válido",
   error="Elíjalo de la lista. Para agregar uno nuevo vaya a CONFIG, columna N.",
   promptTitle="Punto de ocurrencia", prompt="En qué parte de la operación se rompió.",
   showInputMessage=True, **LISTA)
dv(nv, R_NOV("P"), formula1="CAUSAS_RAIZ", errorTitle="Causa no válida",
   error="Elíjala de la lista. Para agregar una nueva vaya a CONFIG, columna G.",
   promptTitle="Causa raíz", prompt="Por qué pasó. Define la familia 6M y el área responsable.",
   showInputMessage=True, **LISTA)
dv(nv, R_NOV("U"), formula1="ESTADOS_NOVEDAD", errorTitle="Estado no válido",
   error="Elíjalo de la lista. Para agregar uno nuevo vaya a CONFIG, columna K.",
   promptTitle="Estado", prompt="Los estados con ¿CIERRA EL CASO? = SÍ detienen el conteo de días.",
   showInputMessage=True, **LISTA)
dv(nv, R_NOV("V"), formula1="RESPONSABLES", errorTitle="Responsable no válido",
   error="Elíjalo de la lista (CONFIG, columna T).", **LISTA)
dv(nv, R_NOV("B"), type="date", operator="between", formula1="DATE(2020,1,1)", formula2="DATE(2040,12,31)",
   allow_blank=True, showErrorMessage=True, errorTitle="Fecha no válida", error="Escriba una fecha real (dd/mm/aaaa).")
dv(nv, R_NOV("X"), type="custom", formula1=f'OR($X{NOV0}="",AND(ISNUMBER($X{NOV0}),$X{NOV0}>=$B{NOV0}))',
   allow_blank=True, showErrorMessage=True, errorTitle="Fecha de solución inválida",
   error="No puede ser anterior a la fecha de la novedad.")
for col in ("S", "T"):
    dv(nv, R_NOV(col), type="decimal", operator="greaterThanOrEqual", formula1="0", allow_blank=True,
       showErrorMessage=True, errorTitle="Valor inválido", error="Debe ser un número mayor o igual a 0.")

dv(ev, R_ENV("E"), warn=True, formula1="TRANSPORTADORAS", errorTitle="Transportadora nueva",
   error="No está en CONFIG. Si es correcta, agréguela en CONFIG columna R para que entre al tablero.", **LISTA)
for col in ("B", "J", "K"):
    dv(ev, R_ENV(col), warn=True, type="date", operator="between", formula1="DATE(2020,1,1)",
       formula2="DATE(2040,12,31)", allow_blank=True, showErrorMessage=True,
       errorTitle="Fecha no válida", error="Escriba una fecha real (dd/mm/aaaa).")
for col in ("H", "I"):
    dv(ev, R_ENV(col), warn=True, type="decimal", operator="greaterThanOrEqual", formula1="0", allow_blank=True,
       showErrorMessage=True, errorTitle="Valor inválido", error="Debe ser un número mayor o igual a 0.")

# ---------------- formato condicional ----------------
def txt_rule(ws, rng, valor, bg, tx, size=10, bold=True):
    ws.conditional_formatting.add(rng, CellIsRule(operator="equal", formula=[f'"{valor}"'],
        fill=fl(bg), font=Font(name=FN, size=size, bold=bold, color=tx)))

def fx_rule(ws, rng, formula, bg=None, tx=None, size=10, bold=True):
    ws.conditional_formatting.add(rng, FormulaRule(formula=[formula],
        fill=(fl(bg) if bg else None),
        font=Font(name=FN, size=size, bold=bold, color=(tx or INK))))

def num_rule(ws, rng, op, vals, bg, tx, size=10):
    ws.conditional_formatting.add(rng, CellIsRule(operator=op, formula=vals,
        fill=fl(bg), font=Font(name=FN, size=size, bold=True, color=tx)))

# --- NOVEDADES ---  (las columnas se corrieron al entrar Origen y Punto de ocurrencia)
for v, bg, tx in [("En plazo", OK_BG, OK_TX), ("Por vencer", WARN_BG, WARN_TX),
                  ("Vencida", DANG_BG, DANG_TX), ("Resuelta a tiempo", INFO_BG, INFO_TX),
                  ("Resuelta tarde", "FFFFE4C4", "FF9A3412"), ("Resuelta", MUTE_BG, MUTE_TX),
                  ("Sin clasificar", MUTE_BG, MUTE_TX)]:
    txt_rule(nv, R_NOV("Z"), v, bg, tx)
for v, bg, tx in [("Crítica", "FF991B1B", WHITE), ("Alta", DANG_BG, DANG_TX),
                  ("Media", WARN_BG, WARN_TX), ("Baja", OK_BG, OK_TX)]:
    txt_rule(nv, R_NOV("M"), v, bg, tx)
txt_rule(nv, R_NOV("N"), "SÍ", WARN_BG, WARN_TX)
txt_rule(nv, R_NOV("C"), "Interna", INFO_BG, INFO_TX)
txt_rule(nv, R_NOV("C"), "En ruta", MUTE_BG, MUTE_TX)
txt_rule(nv, R_NOV("E"), "OK", OK_BG, OK_TX)
txt_rule(nv, R_NOV("E"), "NO EXISTE", DANG_BG, DANG_TX)
txt_rule(nv, R_NOV("E"), "FALTA GUÍA", DANG_BG, DANG_TX)
txt_rule(nv, R_NOV("E"), "DUPLICADA", WARN_BG, WARN_TX)
txt_rule(nv, R_NOV("E"), "Sin guía (interna)", MUTE_BG, MUTE_TX, bold=False)
CIERRA = f'IFERROR(INDEX({C("L")},MATCH($U{NOV0},{C("K")},0)),"NO")'
fx_rule(nv, R_NOV("U"), f'$U{NOV0}="Sin gestionar"', DANG_BG, DANG_TX)
fx_rule(nv, R_NOV("U"), f'AND($U{NOV0}<>"",{CIERRA}="SÍ")', OK_BG, OK_TX)
fx_rule(nv, R_NOV("U"), f'AND($U{NOV0}<>"",{CIERRA}="NO")', WARN_BG, WARN_TX)
fx_rule(nv, R_NOV("X"), f'AND($X{NOV0}="",$Z{NOV0}="Resuelta")', DANG_BG, DANG_TX)
nv.conditional_formatting.add(R_NOV("T"), DataBarRule(start_type="num", start_value=0,
    end_type="percentile", end_value=95, color=AMBER[2:], showValue=True))
nv.conditional_formatting.add(R_NOV("Y"), DataBarRule(start_type="num", start_value=0,
    end_type="percentile", end_value=95, color="94A3B8", showValue=True))
fx_rule(nv, f"A{NOV0}:AB{NOV1}", f'$Z{NOV0}="Vencida"', None, DANG_TX)

# --- ENVIOS ---
for v, bg, tx in [("Sí", OK_BG, OK_TX), ("No", DANG_BG, DANG_TX),
                  ("En ruta", MUTE_BG, MUTE_TX), ("Atrasado", DANG_BG, DANG_TX)]:
    txt_rule(ev, R_ENV("M"), v, bg, tx)
txt_rule(ev, R_ENV("O"), "Sí", OK_BG, OK_TX); txt_rule(ev, R_ENV("O"), "No", DANG_BG, DANG_TX)
txt_rule(ev, R_ENV("P"), "OTIF", OK_BG, OK_TX); txt_rule(ev, R_ENV("P"), "Falló", DANG_BG, DANG_TX)
num_rule(ev, R_ENV("N"), "greaterThan", ["0"], WARN_BG, WARN_TX)
fx_rule(ev, f"A{ENV0}:P{ENV1}", f'AND($A{ENV0}<>"",COUNTIFS($A${ENV0}:$A${ENV1},$A{ENV0})>1)', None, "FF9A3412")

# --- TABLERO ---
K18 = 18
for coord, op, vals, bg, tx in [
    ("D7","greaterThanOrEqual",["0.95"],OK_BG,OK_TX), ("D7","lessThan",["0.9"],DANG_BG,DANG_TX),
    ("F7","greaterThanOrEqual",["0.95"],OK_BG,OK_TX), ("F7","lessThan",["0.9"],DANG_BG,DANG_TX),
    ("H7","greaterThan",["0.05"],DANG_BG,DANG_TX),    ("H7","lessThanOrEqual",["0.03"],OK_BG,OK_TX),
    ("H10","greaterThan",["0"],DANG_BG,DANG_TX),      ("F10","greaterThan",["0"],WARN_BG,WARN_TX),
    ("L10","lessThan",["0.9"],DANG_BG,DANG_TX),       ("L10","greaterThanOrEqual",["0.9"],OK_BG,OK_TX),
    ("H13","greaterThan",["0.3"],WARN_BG,WARN_TX),    ("F13","greaterThan",["0"],INFO_BG,INFO_TX)]:
    num_rule(tb, coord, op, vals, bg, tx, size=K18)
for v, bg, tx in [("A", OK_BG, OK_TX), ("B", INFO_BG, INFO_TX), ("C", WARN_BG, WARN_TX), ("D", DANG_BG, DANG_TX)]:
    txt_rule(tb, "M18:M27", v, bg, tx)
num_rule(tb, "E18:E27", "greaterThanOrEqual", ["0.95"], OK_BG, OK_TX)
num_rule(tb, "E18:E27", "lessThan", ["0.9"], DANG_BG, DANG_TX)
num_rule(tb, "G18:G27", "greaterThan", ["0.05"], DANG_BG, DANG_TX)
num_rule(tb, "I18:I27", "greaterThan", ["0"], DANG_BG, DANG_TX)
tb.conditional_formatting.add("L18:L27", DataBarRule(start_type="num", start_value=0,
    end_type="num", end_value=100, color="2563EB", showValue=True))
num_rule(tb, "F33:F44", "lessThanOrEqual", ["0.8"], WARN_BG, WARN_TX)
for rng in ("D33:D44", "D49:D80", "D86:D97", "I102:I109"):
    tb.conditional_formatting.add(rng, DataBarRule(start_type="num", start_value=0,
        end_type="percentile", end_value=100, color="2563EB", showValue=True))
for v, bg, tx in [("Crítica","FF991B1B",WHITE),("Alta",DANG_BG,DANG_TX),("Media",WARN_BG,WARN_TX),("Baja",OK_BG,OK_TX)]:
    txt_rule(tb, "H49:H80", v, bg, tx)
txt_rule(tb, "G49:G80", "Interna", INFO_BG, INFO_TX)
txt_rule(tb, "G49:G80", "En ruta", MUTE_BG, MUTE_TX)
num_rule(tb, "J49:J80", "greaterThan", ["0"], DANG_BG, DANG_TX)
num_rule(tb, "H86:H97", "greaterThan", ["0"], DANG_BG, DANG_TX)
for v, bg, tx in [("Sí", OK_BG, OK_TX), ("No", DANG_BG, DANG_TX), ("OTIF", OK_BG, OK_TX),
                  ("Falló", DANG_BG, DANG_TX), ("En ruta", MUTE_BG, MUTE_TX), ("Atrasado", DANG_BG, DANG_TX),
                  ("Vencida", DANG_BG, DANG_TX), ("En plazo", OK_BG, OK_TX), ("Por vencer", WARN_BG, WARN_TX),
                  ("Resuelta a tiempo", INFO_BG, INFO_TX), ("Resuelta tarde", "FFFFE4C4", "FF9A3412")]:
    txt_rule(tb, "D115:D130", v, bg, tx)

# =========================================================================
# GRAFICAS DEL TABLERO
# =========================================================================
from openpyxl.chart import BarChart, Reference
from openpyxl.chart.label import DataLabelList
from openpyxl.drawing.line import LineProperties
from openpyxl.chart.shapes import GraphicalProperties

widths(tb, {"N":2,"O":13,"P":13,"Q":13,"R":13,"S":13,"T":13,"U":13,"V":13})

def grafica(titulo, cat_ini, cat_fin, val_col, val_ini, val_fin, ancla,
            horizontal=False, alto=7.5, ancho=15.5, fmt=None, color="2563EB"):
    ch = BarChart()
    ch.type = "bar" if horizontal else "col"
    ch.style = None
    ch.title = titulo
    ch.legend = None
    ch.gapWidth = 45
    ch.add_data(Reference(tb, min_col=ci(val_col), min_row=val_ini, max_row=val_fin), titles_from_data=False)
    ch.set_categories(Reference(tb, min_col=2, min_row=cat_ini, max_row=cat_fin))
    s = ch.series[0]
    s.graphicalProperties = GraphicalProperties(solidFill=color)
    s.graphicalProperties.line = LineProperties(noFill=True)
    ch.dLbls = DataLabelList(); ch.dLbls.showVal = True; ch.dLbls.showSerName = False
    ch.dLbls.showCatName = False; ch.dLbls.showLegendKey = False
    if fmt: ch.dLbls.numFmt = fmt
    ch.y_axis.majorGridlines = None
    ch.x_axis.majorGridlines = None
    ch.y_axis.delete = False; ch.x_axis.delete = False
    if fmt: ch.y_axis.numFmt = fmt
    ch.height = alto; ch.width = ancho
    tb.add_chart(ch, ancla)
    return ch

# Alto en cm -> filas: una fila estandar mide ~0,53 cm. Se deja aire entre
# graficas para que no se monten unas sobre otras.
grafica("OTIF por transportadora", 18,  27, "E", 18,  27, "O17",  fmt="0%", alto=8.5)      # 17-33
grafica("Causas que más pesan",    33,  44, "D", 33,  44, "O35",  horizontal=True, alto=11.5)  # 35-57
grafica("Novedades por tipo",      49,  80, "D", 49,  80, "O59",  horizontal=True, alto=18.0)  # 59-93
grafica("Dónde se rompe la operación", 86, 97, "D", 86, 97, "O95", horizontal=True, alto=11.5,
        color="0F766E")  # 95-117
grafica("Estado de la gestión",    102, 107, "D", 102, 107, "O119", horizontal=True, alto=6.5,
        color="D97706")  # 119-131

put(tb, "O15", "Las gráficas se recalculan con el periodo de arriba.", font=f_note, al=LEF, box=False)
tb.merge_cells("O15:V15")
# =========================================================================
# PROTECCION, ORDEN, GUARDADO
# =========================================================================
for ws in (ev, nv, tb, ini):
    p = ws.protection
    p.sheet = True
    p.autoFilter = False; p.sort = False; p.formatColumns = False; p.formatRows = False
    p.selectLockedCells = False; p.selectUnlockedCells = False

wb._sheets = [wb[n] for n in ["INICIO", "TABLERO", "NOVEDADES", "ENVIOS", "CONFIG"]]
wb.active = 0
wb.calculation.fullCalcOnLoad = True

OUT = os.environ.get("OUT") or os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                            "MATRIZ_NOVEDADES_LOGISTICA_TRANSPORTE.xlsx")
wb.save(OUT)
print("OK ->", OUT)
