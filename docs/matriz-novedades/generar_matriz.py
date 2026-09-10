# -*- coding: utf-8 -*-
"""MATRIZ DE NOVEDADES - LOGISTICA Y TRANSPORTE

Reconstruye MATRIZ_NOVEDADES_LOGISTICA_TRANSPORTE.xlsx desde cero.
Ver README.md para el detalle de columnas, formulas y KPIs.

    pip install openpyxl
    python3 generar_matriz.py

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
CFG0, CFG1 = 4, 43        # CONFIG   : catalogos fila 4 a 43

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

TIPOS = [  # tipo, gravedad, SLA dias habiles, afecta la entrega (in full)
 ("Cliente ausente / no atiende",          "Media",   2, "SÍ"),
 ("Cliente rechaza el envío",              "Alta",    2, "SÍ"),
 ("Dirección errada o incompleta",         "Media",   2, "SÍ"),
 ("Cliente cerrado / fuera de horario",    "Media",   2, "SÍ"),
 ("Zona restringida o sin acceso",         "Media",   3, "SÍ"),
 ("Pago contraentrega fallido",            "Alta",    2, "SÍ"),
 ("Avería / producto dañado",              "Alta",    3, "SÍ"),
 ("Faltante (llegó de menos)",             "Alta",    2, "SÍ"),
 ("Sobrante (llegó de más)",               "Baja",    5, "NO"),
 ("Producto equivocado",                   "Alta",    2, "SÍ"),
 ("Producto vencido o próximo a vencer",   "Alta",    3, "SÍ"),
 ("Empaque en mal estado",                 "Media",   3, "NO"),
 ("Retraso en vía",                        "Alta",    1, "NO"),
 ("Vehículo varado / falla mecánica",      "Crítica", 1, "SÍ"),
 ("Pérdida o robo de mercancía",           "Crítica", 1, "SÍ"),
 ("Entrega parcial acordada",              "Baja",    5, "SÍ"),
 ("Soporte de entrega sin firmar",         "Media",   4, "NO"),
 ("Error en factura o precio",             "Media",   5, "NO"),
 ("Flete no liquidado",                    "Baja",    5, "NO"),
]
CAUSAS = [  # causa raiz, familia 6M, area responsable
 ("Error de alistamiento (picking)",            "Método",        "Bodega"),
 ("Embalaje o estibado deficiente",             "Material",      "Bodega"),
 ("Inventario descuadrado",                     "Medición",      "Bodega"),
 ("Manipulación brusca en cargue/descargue",    "Mano de obra",  "Transporte"),
 ("Sobrecupo o mal acomodo en el vehículo",     "Método",        "Transporte"),
 ("Conductor sin capacitación o procedimiento", "Mano de obra",  "Transporte"),
 ("Falla mecánica del vehículo",                "Máquina",       "Transporte"),
 ("Ruta mal planeada o secuencia errada",       "Método",        "Planeación"),
 ("Promesa de entrega irreal",                  "Método",        "Planeación"),
 ("Datos del cliente desactualizados",          "Medición",      "Comercial"),
 ("Error de digitación del pedido",             "Mano de obra",  "Comercial"),
 ("Cliente cambió de decisión",                 "Externo",       "Comercial"),
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
TRANSP = ["Transportadora A", "Transportadora B", "Transportadora C", "Flota propia"]
RESPON = ["Coordinador de logística", "Jefe de bodega", "Analista de transporte",
          "Servicio al cliente", "Comercial", "Facturación", "Cartera", "Calidad"]

title(cf, 1, "A", "O", "CONFIG · catálogos y reglas de negocio")
cf["A2"] = ("Aquí se cambia el comportamiento de toda la matriz sin tocar una sola fórmula. "
            "Agregue filas hacia abajo: las listas desplegables crecen solas.")
cf["A2"].font = f_note; cf.merge_cells("A2:O2")

CFG_HDR = [("A","TIPO DE NOVEDAD"),("B","GRAVEDAD"),("C","SLA (días hábiles)"),("D","¿AFECTA LA ENTREGA?"),
           ("F","CAUSA RAÍZ"),("G","FAMILIA (6M)"),("H","ÁREA RESPONSABLE"),
           ("J","ESTADO"),("K","¿CIERRA EL CASO?"),
           ("M","TRANSPORTADORA"),("O","RESPONSABLE")]
for col, tx in CFG_HDR:
    put(cf, f"{col}3", tx, font=f_hdr, fill=AMBER, al=CEN)
cf.row_dimensions[3].height = 30

def col_write(ws, col, row0, vals, fmt=None, al=None):
    for i, v in enumerate(vals):
        put(ws, f"{col}{row0+i}", v, fill=EDIT, fmt=fmt, al=al or LEF, editable=True)

col_write(cf,"A",4,[t[0] for t in TIPOS]); col_write(cf,"B",4,[t[1] for t in TIPOS], al=CEN)
col_write(cf,"C",4,[t[2] for t in TIPOS], NUM, CEN); col_write(cf,"D",4,[t[3] for t in TIPOS], al=CEN)
col_write(cf,"F",4,[c[0] for c in CAUSAS]); col_write(cf,"G",4,[c[1] for c in CAUSAS], al=CEN)
col_write(cf,"H",4,[c[2] for c in CAUSAS], al=CEN)
col_write(cf,"J",4,[e[0] for e in ESTADOS]); col_write(cf,"K",4,[e[1] for e in ESTADOS], al=CEN)
col_write(cf,"M",4,TRANSP); col_write(cf,"O",4,RESPON)

widths(cf, {"A":40,"B":12,"C":15,"D":18,"E":2,"F":40,"G":16,"H":16,"I":2,
            "J":28,"K":16,"L":2,"M":24,"N":2,"O":26})
cf.freeze_panes = "A4"
for r in range(4, CFG1+1): cf.row_dimensions[r].height = 16

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
        ev[f"{col}{r}"] = f.format(r=r, nC=N("C"), nM=N("M"))
ev.freeze_panes = "C4"
ev.auto_filter.ref = f"A3:P{ENV1}"

# =========================================================================
# NOVEDADES  -  la matriz
# =========================================================================
nv = sheet("NOVEDADES", AMBER)
title(nv, 1, "A", "Z", "MATRIZ DE NOVEDADES · logística y transporte")

NOV_COLS = [
 ("A","ID",                    "C", 10, "General", CEN),
 ("B","Fecha de la novedad",   "M", 14, FECHA,     CEN),
 ("C","Nº Guía / Remisión",    "M", 16, "General", CEN),
 ("D","Validación",            "C", 13, "General", CEN),
 ("E","Cliente",               "C", 30, "General", LEF),
 ("F","Ciudad destino",        "C", 17, "General", LEF),
 ("G","Transportadora",        "C", 19, "General", LEF),
 ("H","Conductor",             "C", 21, "General", LEF),
 ("I","Placa",                 "C", 10, "General", CEN),
 ("J","Fecha despacho",        "C", 13, FECHA,     CEN),
 ("K","Tipo de novedad",       "M", 32, "General", LEF),
 ("L","Gravedad",              "C", 11, "General", CEN),
 ("M","¿Afecta la entrega?",   "C", 13, "General", CEN),
 ("N","Causa raíz",            "M", 34, "General", LEF),
 ("O","Familia (6M)",          "C", 15, "General", CEN),
 ("P","Área responsable",      "C", 15, "General", CEN),
 ("Q","Unidades afectadas",    "M", 13, NUM,       CEN),
 ("R","Valor afectado",        "M", 15, MONEY,     RIG),
 ("S","Estado",                "M", 26, "General", LEF),
 ("T","Responsable",           "M", 24, "General", LEF),
 ("U","Fecha límite",          "C", 13, FECHA,     CEN),
 ("V","Fecha de solución",     "M", 14, FECHA,     CEN),
 ("W","Días abiertos",         "C", 11, NUM,       CEN),
 ("X","Estado SLA",            "C", 18, "General", CEN),
 ("Y","Qué se hizo",           "M", 40, "General", LEF),
 ("Z","Notas / soporte",       "M", 34, "General", LEF),
]
banner(nv, 2, "A", "J", "① IDENTIFICAR EL ENVÍO  ·  digite la fecha y el Nº de guía; lo demás se trae solo", BAND_A)
banner(nv, 2, "K", "P", "② CLASIFICAR  ·  qué pasó y por qué", BAND_B)
banner(nv, 2, "Q", "R", "③ IMPACTO", BAND_A)
banner(nv, 2, "S", "X", "④ GESTIONAR Y CERRAR", BAND_B)
banner(nv, 2, "Y", "Z", "⑤ CONSTANCIA", BAND_A)
build_grid(nv, NOV_COLS, NOV0, NOV1)

BUSCA = 'IFERROR(INDEX({rng},MATCH($C{r},{eA},0)),"—")'
FNOV = {
 "A": '=IF($C{r}="","","N-"&TEXT(ROW()-3,"0000"))',
 "D": '=IF($C{r}="","",IF(COUNTIFS({eA},$C{r})=0,"NO EXISTE",IF(COUNTIFS({eA},$C{r})>1,"DUPLICADA","OK")))',
 "E": '=IF($C{r}="","",' + BUSCA.format(rng=E("C"), eA=E("A"), r="{r}") + ')',
 "F": '=IF($C{r}="","",' + BUSCA.format(rng=E("D"), eA=E("A"), r="{r}") + ')',
 "G": '=IF($C{r}="","",' + BUSCA.format(rng=E("E"), eA=E("A"), r="{r}") + ')',
 "H": '=IF($C{r}="","",' + BUSCA.format(rng=E("F"), eA=E("A"), r="{r}") + ')',
 "I": '=IF($C{r}="","",' + BUSCA.format(rng=E("G"), eA=E("A"), r="{r}") + ')',
 "J": '=IF($C{r}="","",IFERROR(INDEX({eB},MATCH($C{r},{eA},0)),""))',
 "L": '=IF($K{r}="","",IFERROR(INDEX({cB},MATCH($K{r},{cA},0)),"Media"))',
 "M": '=IF($K{r}="","",IFERROR(INDEX({cD},MATCH($K{r},{cA},0)),"NO"))',
 "O": '=IF($N{r}="","",IFERROR(INDEX({cG},MATCH($N{r},{cF},0)),"Por definir"))',
 "P": '=IF($N{r}="","",IFERROR(INDEX({cH},MATCH($N{r},{cF},0)),"Por definir"))',
 "U": '=IF(OR($B{r}="",$K{r}=""),"",WORKDAY($B{r},IFERROR(INDEX({cC},MATCH($K{r},{cA},0)),3)))',
 "W": '=IF($B{r}="","",IF($V{r}<>"",$V{r}-$B{r},TODAY()-$B{r}))',
 "X": ('=IF($C{r}="","",IF(IFERROR(INDEX({cK},MATCH($S{r},{cJ},0)),"NO")="SÍ",'
       'IF(OR($V{r}="",$U{r}=""),"Resuelta",IF($V{r}>$U{r},"Resuelta tarde","Resuelta a tiempo")),'
       'IF($U{r}="","Sin clasificar",IF(TODAY()>$U{r},"Vencida",IF(TODAY()>=$U{r}-1,"Por vencer","En plazo")))))'),
}
ARG = dict(eA=E("A"), eB=E("B"), cA=C("A"), cB=C("B"), cC=C("C"), cD=C("D"),
           cF=C("F"), cG=C("G"), cH=C("H"), cJ=C("J"), cK=C("K"))
for r in range(NOV0, NOV1 + 1):
    for col, f in FNOV.items():
        nv[f"{col}{r}"] = f.format(r=r, **ARG)
nv.freeze_panes = "D4"
nv.auto_filter.ref = f"A3:Z{NOV1}"

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
    f'COUNTIFS({N("X")},"{s}",{PN}{extra})' for s in ["En plazo","Por vencer","Vencida","Sin clasificar"])

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

ENTREGADOS = f'(COUNTIFS({E("P")},"OTIF",{PE})+COUNTIFS({E("P")},"Falló",{PE}))'
kpi_row(6, "LO ESENCIAL", [
 ("D","E","OTIF (a tiempo y completo)", f'=IFERROR(COUNTIFS({E("P")},"OTIF",{PE})/{ENTREGADOS},"—")', PCT),
 ("F","G","ENTREGAS A TIEMPO",          f'=IFERROR(COUNTIFS({E("M")},"Sí",{PE})/{ENTREGADOS},"—")', PCT),
 ("H","I","TASA DE NOVEDADES",          f'=IFERROR(COUNTIFS({E("N")},">0",{PE})/COUNTIFS({PE}),"—")', PCT),
 ("J","K","VALOR AFECTADO",             f'=SUMIFS({N("R")},{PN})', MONEY),
 ("L","M","ENVÍOS DEL PERIODO",         f'=COUNTIFS({PE})', NUM),
])
kpi_row(9, "LA GESTIÓN", [
 ("D","E","NOVEDADES",            f'=COUNTIFS({PN})', NUM),
 ("F","G","ABIERTAS",             "=" + ABIERTAS(), NUM),
 ("H","I","VENCIDAS (SLA roto)",  f'=COUNTIFS({N("X")},"Vencida",{PN})', NUM),
 ("J","K","DÍAS PROM. SOLUCIÓN",  f'=IFERROR(ROUND(AVERAGEIFS({N("W")},{PN}),1),0)', DEC),
 ("L","M","CUMPLIMIENTO DE SLA",  f'=IFERROR(COUNTIFS({N("X")},"Resuelta a tiempo",{PN})/COUNTIFS({N("X")},"Resuelta*",{PN}),"—")', PCT),
])

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

# ---- 1. SCORECARD DE TRANSPORTADORAS ----
seccion(tb, 12, "B", "M", "1 · SCORECARD DE TRANSPORTADORAS")
tb["B13"] = ("Nota A = 90 puntos o más · B = 80 a 89 · C = 70 a 79 · D = menos de 70.   "
             "Puntaje = OTIF ×60 + (1 − tasa de novedades) ×25 + (1 − vencidas/novedades) ×15.")
tb["B13"].font = f_note; tb.merge_cells("B13:M13")
thead(14, [("B","Transportadora"),("D","Envíos"),("E","OTIF"),("F","Novedades"),("G","Tasa"),
           ("H","Abiertas"),("I","Vencidas"),("J","Días prom."),("K","Valor afectado"),
           ("L","Puntaje"),("M","Nota")])
tb["C14"].fill = fl(BLUE); tb["C14"].border = BOX; tb.merge_cells("B14:C14")
for r in range(15, 25):
    lr = r - 11
    name_cell(r, f'=IF(CONFIG!$M{lr}="","",CONFIG!$M{lr})')
    g = f'{N("G")},$B{r}'; e = f'{E("E")},$B{r}'
    cell(f"D{r}", f'=IF($B{r}="","",COUNTIFS({e},{PE}))', NUM)
    cell(f"E{r}", f'=IF($B{r}="","",IFERROR(COUNTIFS({e},{E("P")},"OTIF",{PE})/(COUNTIFS({e},{E("P")},"OTIF",{PE})+COUNTIFS({e},{E("P")},"Falló",{PE})),"—"))', PCT1)
    cell(f"F{r}", f'=IF($B{r}="","",COUNTIFS({g},{PN}))', NUM)
    cell(f"G{r}", f'=IF($B{r}="","",IFERROR(COUNTIFS({e},{E("N")},">0",{PE})/$D{r},"—"))', PCT1)
    cell(f"H{r}", f'=IF($B{r}="","",{ABIERTAS(f",{g}")})', NUM)
    cell(f"I{r}", f'=IF($B{r}="","",COUNTIFS({g},{N("X")},"Vencida",{PN}))', NUM)
    cell(f"J{r}", f'=IF($B{r}="","",IFERROR(ROUND(AVERAGEIFS({N("W")},{g},{PN}),1),0))', DEC)
    cell(f"K{r}", f'=IF($B{r}="","",SUMIFS({N("R")},{g},{PN}))', MONEY)
    cell(f"L{r}", f'=IF(OR($B{r}="",$D{r}=0,NOT(ISNUMBER($E{r}))),"—",'
                  f'ROUND($E{r}*60+(1-N($G{r}))*25+IF($F{r}=0,15,(1-$I{r}/$F{r})*15),0))', NUM)
    cell(f"M{r}", f'=IF(NOT(ISNUMBER($L{r})),"—",IF($L{r}>=90,"A",IF($L{r}>=80,"B",IF($L{r}>=70,"C","D"))))')
name_cell(25, '="TOTAL"', bold=True)
for col in "DFHI": cell(f"{col}25", f"=SUM(${col}$15:${col}$24)", NUM, bold=True)
cell("E25", f'=IFERROR(COUNTIFS({E("P")},"OTIF",{PE})/{ENTREGADOS},"—")', PCT1, bold=True)
cell("G25", f'=IFERROR(COUNTIFS({E("N")},">0",{PE})/COUNTIFS({PE}),"—")', PCT1, bold=True)
cell("J25", f'=IFERROR(ROUND(AVERAGEIFS({N("W")},{PN}),1),0)', DEC, bold=True)
cell("K25", "=SUM($K$15:$K$24)", MONEY, bold=True)
cell("L25", "", bold=True); cell("M25", "", bold=True)

# ---- 2. PARETO DE CAUSA RAIZ ----
seccion(tb, 27, "B", "M", "2 · PARETO DE CAUSA RAÍZ — dónde atacar primero")
tb["B28"] = ("Regla 80/20: las causas que aparecen hasta llegar a 80% en la columna «% acumulado» "
             "son las que explican casi todas sus novedades. Empiece por ahí.")
tb["B28"].font = f_note; tb.merge_cells("B28:M28")
thead(29, [("B","Causa raíz"),("D","Casos"),("E","% de las novedades"),("F","% acumulado"),
           ("G","Valor afectado"),("H","Familia (6M)"),("I","Área responsable")])
tb["C29"].fill = fl(BLUE); tb["C29"].border = BOX; tb.merge_cells("B29:C29")
for col in "JKLM":
    put(tb, f"{col}29", None, font=f_hdr, fill=BLUE, al=CEN)
HELP = "CONFIG!$Q$4:$Q$23"; CAUS = "CONFIG!$F$4:$F$23"
for r in range(30, 42):
    k = r - 29
    name_cell(r, f'=IFERROR(INDEX({CAUS},MATCH(LARGE({HELP},{k}),{HELP},0)),"")')
    cell(f"D{r}", f'=IF($B{r}="","",ROUNDDOWN(LARGE({HELP},{k}),0))', NUM)
    cell(f"E{r}", f'=IF($B{r}="","",IFERROR($D{r}/$D$42,0))', PCT1)
    cell(f"F{r}", f'=IF($B{r}="","",IFERROR(SUM($D$30:$D{r})/$D$42,0))', PCT1)
    cell(f"G{r}", f'=IF($B{r}="","",SUMIFS({N("R")},{N("N")},$B{r},{PN}))', MONEY)
    cell(f"H{r}", f'=IF($B{r}="","",IFERROR(INDEX({C("G")},MATCH($B{r},{C("F")},0)),""))')
    cell(f"I{r}", f'=IF($B{r}="","",IFERROR(INDEX({C("H")},MATCH($B{r},{C("F")},0)),""))')
    for col in "JKLM": cell(f"{col}{r}", None)
name_cell(42, '="TOTAL de novedades del periodo"', bold=True)
cell("D42", f'=COUNTIFS({PN})', NUM, bold=True)
cell("E42", '=IF($D$42=0,0,1)', PCT1, bold=True); cell("F42", "", bold=True)
cell("G42", f'=SUMIFS({N("R")},{PN})', MONEY, bold=True)
for col in "HIJKLM": cell(f"{col}42", None, bold=True)

# ---- 3. NOVEDADES POR TIPO ----
seccion(tb, 44, "B", "M", "3 · NOVEDADES POR TIPO — qué está pasando")
thead(45, [("B","Tipo de novedad"),("D","Casos"),("E","% del total"),("F","Valor afectado"),
           ("G","Gravedad"),("H","¿Afecta la entrega?"),("I","Abiertas"),("J","Vencidas"),("K","Días prom.")])
tb["C45"].fill = fl(BLUE); tb["C45"].border = BOX; tb.merge_cells("B45:C45")
for col in "LM": put(tb, f"{col}45", None, font=f_hdr, fill=BLUE, al=CEN)
for r in range(46, 65):
    lr = r - 42
    name_cell(r, f'=IF(CONFIG!$A{lr}="","",CONFIG!$A{lr})')
    t = f'{N("K")},$B{r}'
    cell(f"D{r}", f'=IF($B{r}="","",COUNTIFS({t},{PN}))', NUM)
    cell(f"E{r}", f'=IF($B{r}="","",IFERROR($D{r}/$D$65,0))', PCT1)
    cell(f"F{r}", f'=IF($B{r}="","",SUMIFS({N("R")},{t},{PN}))', MONEY)
    cell(f"G{r}", f'=IF($B{r}="","",IFERROR(INDEX({C("B")},MATCH($B{r},{C("A")},0)),""))')
    cell(f"H{r}", f'=IF($B{r}="","",IFERROR(INDEX({C("D")},MATCH($B{r},{C("A")},0)),""))')
    cell(f"I{r}", f'=IF($B{r}="","",{ABIERTAS(f",{t}")})', NUM)
    cell(f"J{r}", f'=IF($B{r}="","",COUNTIFS({t},{N("X")},"Vencida",{PN}))', NUM)
    cell(f"K{r}", f'=IF($B{r}="","",IFERROR(ROUND(AVERAGEIFS({N("W")},{t},{PN}),1),0))', DEC)
    for col in "LM": cell(f"{col}{r}", None)
name_cell(65, '="TOTAL"', bold=True)
for col in "DIJ": cell(f"{col}65", f"=SUM(${col}$46:${col}$64)", NUM, bold=True)
cell("E65", '=IF($D$65=0,0,1)', PCT1, bold=True)
cell("F65", "=SUM($F$46:$F$64)", MONEY, bold=True)
cell("K65", f'=IFERROR(ROUND(AVERAGEIFS({N("W")},{PN}),1),0)', DEC, bold=True)
for col in "GHLM": cell(f"{col}65", None, bold=True)

# ---- 4. ESTADO DE LA GESTION  +  FAMILIA 6M ----
seccion(tb, 67, "B", "M", "4 · ESTADO DE LA GESTIÓN  y  FAMILIA DE LA CAUSA (6M de Ishikawa)")
thead(68, [("B","Estado"),("D","Casos"),("E","% del total"),
           ("G","Familia (6M)"),("I","Casos"),("J","% del total"),("K","Valor afectado")])
tb["C68"].fill = fl(BLUE); tb["C68"].border = BOX; tb.merge_cells("B68:C68")
tb["H68"].fill = fl(BLUE); tb["H68"].border = BOX; tb.merge_cells("G68:H68")
for col in "FLM": put(tb, f"{col}68", None, font=f_hdr, fill=BLUE, al=CEN)
FAMILIAS = ["Método","Material","Medición","Mano de obra","Máquina","Medio ambiente","Externo","Por definir"]
for r in range(69, 77):
    i = r - 69
    if i < 6:
        lr = r - 65
        name_cell(r, f'=IF(CONFIG!$J{lr}="","",CONFIG!$J{lr})')
        cell(f"D{r}", f'=IF($B{r}="","",COUNTIFS({N("S")},$B{r},{PN}))', NUM)
        cell(f"E{r}", f'=IF($B{r}="","",IFERROR($D{r}/$D$77,0))', PCT1)
    else:
        name_cell(r, None); cell(f"D{r}", None); cell(f"E{r}", None)
    put(tb, f"F{r}", None, fill=CALC, al=CEN)
    g = put(tb, f"G{r}", FAMILIAS[i], fill=CALC, al=LEF)
    put(tb, f"H{r}", None, fill=CALC, al=LEF); tb.merge_cells(f"G{r}:H{r}")
    cell(f"I{r}", f'=COUNTIFS({N("O")},$G{r},{PN})', NUM)
    cell(f"J{r}", f'=IFERROR($I{r}/$I$77,0)', PCT1)
    cell(f"K{r}", f'=SUMIFS({N("R")},{N("O")},$G{r},{PN})', MONEY)
    for col in "LM": cell(f"{col}{r}", None)
name_cell(77, '="TOTAL"', bold=True)
cell("D77", "=SUM($D$69:$D$74)", NUM, bold=True); cell("E77", '=IF($D$77=0,0,1)', PCT1, bold=True)
put(tb, "F77", None, fill=CARD, al=CEN)
put(tb, "G77", "TOTAL", font=f_bold, fill=CARD, al=LEF); put(tb, "H77", None, fill=CARD)
tb.merge_cells("G77:H77")
cell("I77", "=SUM($I$69:$I$76)", NUM, bold=True); cell("J77", '=IF($I$77=0,0,1)', PCT1, bold=True)
cell("K77", "=SUM($K$69:$K$76)", MONEY, bold=True)
for col in "LM": cell(f"{col}77", None, bold=True)

# ---- 5. BUSCADOR DE GUIA ----
seccion(tb, 79, "B", "M", "5 · BUSCADOR — la ficha completa de un envío")
put(tb, "B80", "Escriba el Nº de guía →", font=f_bold, fill=CARD, al=LEF)
put(tb, "C80", None, fill=CARD); tb.merge_cells("B80:C80")
q = put(tb, "D80", None, font=Font(name=FN, size=12, bold=True, color=INK), fill=EDIT, al=CEN, editable=True)
put(tb, "E80", None, fill=EDIT, editable=True); tb.merge_cells("D80:E80")
put(tb, "F80", "◄ la ficha de abajo se llena sola", font=f_note, al=LEF, box=False)
tb.merge_cells("F80:M80"); tb.row_dimensions[80].height = 22

LK = lambda rng: f'IFERROR(INDEX({rng},MATCH($D$80,{E("A")},0)),"—")'
FICHA = [
 ("Cliente",               f'=IF($D$80="","—",{LK(E("C"))})', "General"),
 ("Ciudad destino",        f'=IF($D$80="","—",{LK(E("D"))})', "General"),
 ("Transportadora",        f'=IF($D$80="","—",{LK(E("E"))})', "General"),
 ("Conductor",             f'=IF($D$80="","—",{LK(E("F"))})', "General"),
 ("Placa",                 f'=IF($D$80="","—",{LK(E("G"))})', "General"),
 ("Fecha despacho",        f'=IF($D$80="","—",{LK(E("B"))})', FECHA),
 ("Fecha promesa",         f'=IF($D$80="","—",{LK(E("J"))})', FECHA),
 ("Fecha entrega real",    f'=IF($D$80="","—",{LK(E("K"))})', FECHA),
 ("¿Llegó a tiempo?",      f'=IF($D$80="","—",{LK(E("M"))})', "General"),
 ("¿Llegó completa?",      f'=IF($D$80="","—",{LK(E("O"))})', "General"),
 ("OTIF",                  f'=IF($D$80="","—",{LK(E("P"))})', "General"),
 ("Novedades registradas", f'=IF($D$80="","—",COUNTIFS({N("C")},$D$80))', NUM),
 ("Valor afectado",        f'=IF($D$80="","—",SUMIFS({N("R")},{N("C")},$D$80))', MONEY),
 ("Última novedad",        f'=IF($D$80="","—",IFERROR(LOOKUP(2,1/({N("C")}=$D$80),{N("K")}),"—"))', "General"),
 ("Estado de esa novedad", f'=IF($D$80="","—",IFERROR(LOOKUP(2,1/({N("C")}=$D$80),{N("S")}),"—"))', "General"),
 ("Estado SLA",            f'=IF($D$80="","—",IFERROR(LOOKUP(2,1/({N("C")}=$D$80),{N("X")}),"—"))', "General"),
]
for i, (lbl, frm, fmt) in enumerate(FICHA):
    r = 82 + i
    put(tb, f"B{r}", lbl, font=f_base, fill=CARD, al=LEF)
    put(tb, f"C{r}", None, fill=CARD); tb.merge_cells(f"B{r}:C{r}")
    put(tb, f"D{r}", frm, font=f_bold, fill=CALC, fmt=fmt, al=LEF)
    for col in "EF": put(tb, f"{col}{r}", None, fill=CALC)
    tb.merge_cells(f"D{r}:F{r}")
    tb.row_dimensions[r].height = 16
tb.freeze_panes = "B5"

# ---- columna auxiliar del Pareto, en CONFIG ----
put(cf, "Q3", "⚙ CÁLCULO DEL TABLERO — no borrar", font=f_hdr, fill=INK2, al=CEN)
cf.column_dimensions["P"].width = 2; cf.column_dimensions["Q"].width = 30
for r in range(4, 24):
    put(cf, f"Q{r}", f'=IF($F{r}="","",COUNTIFS({N("N")},$F{r},{N("B")},">="&TABLERO!$E$4,'
                     f'{N("B")},"<="&TABLERO!$G$4)+ROW()/100000)',
        font=f_base, fill=CALC, fmt="0.00000", al=CEN)

# =========================================================================
# INICIO
# =========================================================================
ini = sheet("INICIO", "FF16A34A")
widths(ini, {"A":2, "B":6, "C":148})
GUIA = [
 ("T", "", "MATRIZ DE NOVEDADES · LOGÍSTICA Y TRANSPORTE"),
 ("P", "", "Un solo archivo para registrar todo lo que sale mal en una entrega, saber a quién cobrárselo y medir si está mejorando."),
 ("H", "", "CÓMO SE USA — TRES PASOS"),
 ("S", "1", "ENVÍOS.  Cada despacho es una fila. Escriba guía, fecha, cliente, ciudad, transportadora, conductor, placa, unidades, valor y la FECHA PROMESA DE ENTREGA. Cuando llegue, escriba la fecha de entrega real. Con eso el archivo calcula solo si llegó a tiempo y si llegó completo."),
 ("S", "2", "NOVEDADES.  ¿Algo salió mal? Escriba la fecha y el Nº de guía: cliente, ciudad, transportadora, conductor, placa y fecha de despacho se traen solos. Usted solo elige el tipo, la causa, cuánto costó, el estado y quién responde."),
 ("S", "3", "TABLERO.  Ponga el periodo arriba y lea. Le dice su OTIF, qué transportadora rinde y cuál no, y cuáles causas explican el 80% de sus problemas."),
 ("H", "", "LA REGLA DE COLORES"),
 ("P", "", "AMARILLO = usted lo escribe.        GRIS = se calcula solo, no lo toque.        Encabezado dorado = columna de captura.        Encabezado azul = columna calculada."),
 ("P", "", "Además, cada hoja tiene una banda oscura arriba que separa las zonas: lo que se digita, lo que se calcula y lo que es seguimiento."),
 ("H", "", "LOS CUATRO NÚMEROS QUE IMPORTAN"),
 ("P", "", "OTIF (On Time In Full): de los envíos ya entregados, cuántos llegaron a tiempo Y completos. Es el estándar de la industria; una operación sana anda por encima del 95%."),
 ("P", "", "TASA DE NOVEDADES: de cada 100 envíos, cuántos tuvieron algún problema. Cuenta envíos afectados, no novedades, para que no se infle cuando un envío genera tres."),
 ("P", "", "CUMPLIMIENTO DE SLA: de las novedades ya resueltas, cuántas se resolvieron dentro del plazo que usted mismo definió por tipo."),
 ("P", "", "PUNTAJE Y NOTA POR TRANSPORTADORA: A, B, C o D. Es la hoja que se lleva a la reunión de negociación."),
 ("H", "", "CÓMO CAMBIAR LAS REGLAS SIN TOCAR FÓRMULAS"),
 ("P", "", "Todo vive en la hoja CONFIG: los tipos de novedad con su gravedad y su plazo en días hábiles, las causas raíz con su familia 6M y su área responsable, los estados y cuáles cierran el caso, las transportadoras y los responsables."),
 ("P", "", "Agregue filas hacia abajo y listo: las listas desplegables crecen solas y el tablero las recoge en el siguiente cálculo. Reemplace «Transportadora A, B, C» por los nombres reales antes de empezar."),
 ("H", "", "SOBRE LA CAUSA RAÍZ (LAS 6M)"),
 ("P", "", "Cada causa está clasificada en una de las seis familias del diagrama de Ishikawa: Método, Material, Medición, Mano de obra, Máquina y Medio ambiente (más Externo y Por definir). Sirve para ver si sus problemas son de proceso, de gente, de equipos o de afuera — y esa respuesta cambia qué se hace al respecto."),
 ("H", "", "DETALLES PRÁCTICOS"),
 ("P", "", "Las hojas están protegidas para que nadie borre una fórmula por accidente, pero SIN contraseña: Revisar → Desproteger hoja y ya. Los plazos se cuentan en días hábiles (sin sábados ni domingos); si quiere descontar festivos, agregue una columna de fechas festivas en CONFIG y páselas como tercer argumento de DIA.LAB."),
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
DYN = lambda col: f"OFFSET(CONFIG!${col}$4,0,0,MAX(1,COUNTA(CONFIG!${col}$4:${col}$43)),1)"
for nm, col in [("TIPOS_NOVEDAD","A"), ("CAUSAS_RAIZ","F"), ("ESTADOS_NOVEDAD","J"),
                ("TRANSPORTADORAS","M"), ("RESPONSABLES","O")]:
    wb.defined_names.add(DefinedName(nm, attr_text=DYN(col)))

def dv(ws, rng, warn=False, **kw):
    d = DataValidation(**kw); ws.add_data_validation(d); d.add(rng)
    if warn: d.errorStyle = "warning"
    return d

R_NOV = lambda c: f"{c}{NOV0}:{c}{NOV1}"
R_ENV = lambda c: f"{c}{ENV0}:{c}{ENV1}"
LISTA = dict(type="list", allow_blank=True, showErrorMessage=True)
dv(nv, R_NOV("K"), formula1="TIPOS_NOVEDAD", errorTitle="Tipo no válido",
   error="Elíjalo de la lista. Para agregar uno nuevo vaya a CONFIG, columna A.",
   promptTitle="Tipo de novedad", prompt="Define la gravedad y el plazo (SLA).", showInputMessage=True, **LISTA)
dv(nv, R_NOV("N"), formula1="CAUSAS_RAIZ", errorTitle="Causa no válida",
   error="Elíjala de la lista. Para agregar una nueva vaya a CONFIG, columna F.",
   promptTitle="Causa raíz", prompt="Por qué pasó. Define la familia 6M y el área responsable.",
   showInputMessage=True, **LISTA)
dv(nv, R_NOV("S"), formula1="ESTADOS_NOVEDAD", errorTitle="Estado no válido",
   error="Elíjalo de la lista. Para agregar uno nuevo vaya a CONFIG, columna J.",
   promptTitle="Estado", prompt="Los estados con ¿CIERRA EL CASO? = SÍ detienen el conteo de días.",
   showInputMessage=True, **LISTA)
dv(nv, R_NOV("T"), formula1="RESPONSABLES", errorTitle="Responsable no válido",
   error="Elíjalo de la lista (CONFIG, columna O).", **LISTA)
dv(nv, R_NOV("B"), type="date", operator="between", formula1="DATE(2020,1,1)", formula2="DATE(2040,12,31)",
   allow_blank=True, showErrorMessage=True, errorTitle="Fecha no válida", error="Escriba una fecha real (dd/mm/aaaa).")
dv(nv, R_NOV("V"), type="custom", formula1=f'OR($V{NOV0}="",AND(ISNUMBER($V{NOV0}),$V{NOV0}>=$B{NOV0}))',
   allow_blank=True, showErrorMessage=True, errorTitle="Fecha de solución inválida",
   error="No puede ser anterior a la fecha de la novedad.")
for col in ("Q", "R"):
    dv(nv, R_NOV(col), type="decimal", operator="greaterThanOrEqual", formula1="0", allow_blank=True,
       showErrorMessage=True, errorTitle="Valor inválido", error="Debe ser un número mayor o igual a 0.")

dv(ev, R_ENV("E"), warn=True, formula1="TRANSPORTADORAS", errorTitle="Transportadora nueva",
   error="No está en CONFIG. Si es correcta, agréguela en CONFIG columna M para que entre al tablero.", **LISTA)
for col in ("B", "J", "K"):
    dv(ev, R_ENV(col), warn=True, type="date", operator="between", formula1="DATE(2020,1,1)",
       formula2="DATE(2040,12,31)", allow_blank=True, showErrorMessage=True,
       errorTitle="Fecha no válida", error="Escriba una fecha real (dd/mm/aaaa).")
for col in ("H", "I"):
    dv(ev, R_ENV(col), warn=True, type="decimal", operator="greaterThanOrEqual", formula1="0", allow_blank=True,
       showErrorMessage=True, errorTitle="Valor inválido", error="Debe ser un número mayor o igual a 0.")

# ---------------- formato condicional ----------------
def txt_rule(ws, rng, valor, bg, tx, size=10):
    ws.conditional_formatting.add(rng, CellIsRule(operator="equal", formula=[f'"{valor}"'],
        fill=fl(bg), font=Font(name=FN, size=size, bold=True, color=tx)))

def fx_rule(ws, rng, formula, bg=None, tx=None, size=10, bold=True):
    ws.conditional_formatting.add(rng, FormulaRule(formula=[formula],
        fill=(fl(bg) if bg else None),
        font=Font(name=FN, size=size, bold=bold, color=(tx or INK))))

def num_rule(ws, rng, op, vals, bg, tx, size=10):
    ws.conditional_formatting.add(rng, CellIsRule(operator=op, formula=vals,
        fill=fl(bg), font=Font(name=FN, size=size, bold=True, color=tx)))

# --- NOVEDADES ---
for v, bg, tx in [("En plazo", OK_BG, OK_TX), ("Por vencer", WARN_BG, WARN_TX),
                  ("Vencida", DANG_BG, DANG_TX), ("Resuelta a tiempo", INFO_BG, INFO_TX),
                  ("Resuelta tarde", "FFFFE4C4", "FF9A3412"), ("Resuelta", MUTE_BG, MUTE_TX),
                  ("Sin clasificar", MUTE_BG, MUTE_TX)]:
    txt_rule(nv, R_NOV("X"), v, bg, tx)
for v, bg, tx in [("Crítica", "FF991B1B", WHITE), ("Alta", DANG_BG, DANG_TX),
                  ("Media", WARN_BG, WARN_TX), ("Baja", OK_BG, OK_TX)]:
    txt_rule(nv, R_NOV("L"), v, bg, tx)
txt_rule(nv, R_NOV("M"), "SÍ", WARN_BG, WARN_TX)
txt_rule(nv, R_NOV("D"), "OK", OK_BG, OK_TX)
txt_rule(nv, R_NOV("D"), "NO EXISTE", DANG_BG, DANG_TX)
txt_rule(nv, R_NOV("D"), "DUPLICADA", WARN_BG, WARN_TX)
CIERRA = f'IFERROR(INDEX({C("K")},MATCH($S{NOV0},{C("J")},0)),"NO")'
fx_rule(nv, R_NOV("S"), f'$S{NOV0}="Sin gestionar"', DANG_BG, DANG_TX)
fx_rule(nv, R_NOV("S"), f'AND($S{NOV0}<>"",{CIERRA}="SÍ")', OK_BG, OK_TX)
fx_rule(nv, R_NOV("S"), f'AND($S{NOV0}<>"",{CIERRA}="NO")', WARN_BG, WARN_TX)
fx_rule(nv, R_NOV("V"), f'AND($V{NOV0}="",$X{NOV0}="Resuelta")', DANG_BG, DANG_TX)
nv.conditional_formatting.add(R_NOV("R"), DataBarRule(start_type="num", start_value=0,
    end_type="percentile", end_value=95, color=AMBER[2:], showValue=True))
nv.conditional_formatting.add(R_NOV("W"), DataBarRule(start_type="num", start_value=0,
    end_type="percentile", end_value=95, color="94A3B8", showValue=True))
fx_rule(nv, f"A{NOV0}:Z{NOV1}", f'$X{NOV0}="Vencida"', None, DANG_TX)

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
    ("L10","lessThan",["0.9"],DANG_BG,DANG_TX),       ("L10","greaterThanOrEqual",["0.9"],OK_BG,OK_TX)]:
    num_rule(tb, coord, op, vals, bg, tx, size=K18)
for v, bg, tx in [("A", OK_BG, OK_TX), ("B", INFO_BG, INFO_TX), ("C", WARN_BG, WARN_TX), ("D", DANG_BG, DANG_TX)]:
    txt_rule(tb, "M15:M24", v, bg, tx)
num_rule(tb, "E15:E24", "greaterThanOrEqual", ["0.95"], OK_BG, OK_TX)
num_rule(tb, "E15:E24", "lessThan", ["0.9"], DANG_BG, DANG_TX)
num_rule(tb, "G15:G24", "greaterThan", ["0.05"], DANG_BG, DANG_TX)
num_rule(tb, "I15:I24", "greaterThan", ["0"], DANG_BG, DANG_TX)
tb.conditional_formatting.add("L15:L24", DataBarRule(start_type="num", start_value=0,
    end_type="num", end_value=100, color="2563EB", showValue=True))
num_rule(tb, "F30:F41", "lessThanOrEqual", ["0.8"], WARN_BG, WARN_TX)
for rng in ("D30:D41", "D46:D64", "I69:I76"):
    tb.conditional_formatting.add(rng, DataBarRule(start_type="num", start_value=0,
        end_type="percentile", end_value=100, color="2563EB", showValue=True))
for v, bg, tx in [("Crítica","FF991B1B",WHITE),("Alta",DANG_BG,DANG_TX),("Media",WARN_BG,WARN_TX),("Baja",OK_BG,OK_TX)]:
    txt_rule(tb, "G46:G64", v, bg, tx)
txt_rule(tb, "H46:H64", "SÍ", WARN_BG, WARN_TX)
num_rule(tb, "J46:J64", "greaterThan", ["0"], DANG_BG, DANG_TX)
for v, bg, tx in [("Sí", OK_BG, OK_TX), ("No", DANG_BG, DANG_TX), ("OTIF", OK_BG, OK_TX),
                  ("Falló", DANG_BG, DANG_TX), ("En ruta", MUTE_BG, MUTE_TX), ("Atrasado", DANG_BG, DANG_TX),
                  ("Vencida", DANG_BG, DANG_TX), ("En plazo", OK_BG, OK_TX), ("Por vencer", WARN_BG, WARN_TX),
                  ("Resuelta a tiempo", INFO_BG, INFO_TX), ("Resuelta tarde", "FFFFE4C4", "FF9A3412")]:
    txt_rule(tb, "D82:D97", v, bg, tx)

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

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                   "MATRIZ_NOVEDADES_LOGISTICA_TRANSPORTE.xlsx")
wb.save(OUT)
print("OK ->", OUT)
