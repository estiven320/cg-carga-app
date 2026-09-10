# -*- coding: utf-8 -*-
"""Generador: MATRIZ DE NOVEDADES DE LOGISTICA Y TRANSPORTE - GESTOAGRO S.A.S.

Reconstruye MATRIZ_NOVEDADES_LOGISTICA_GESTOAGRO.xlsx desde cero.
Ver ARQUITECTURA.md para la especificacion completa de columnas, formulas,
validaciones, formato condicional y KPIs.

    pip install openpyxl
    python3 generar_matriz.py
"""
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side, Protection
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.datavalidation import DataValidation
from openpyxl.formatting.rule import FormulaRule, CellIsRule, DataBarRule
from openpyxl.workbook.defined_name import DefinedName

# ---------- PARAMETROS DE CAPACIDAD ----------
DESP_R0, DESP_R1 = 3, 3002      # DESPACHOS: datos fila 3 a 3002 (3.000 despachos)
NOV_R0,  NOV_R1  = 4, 2003      # NOVEDADES: datos fila 4 a 2003 (2.000 novedades)
LST_R0,  LST_R1  = 2, 41        # LISTAS: catalogos fila 2 a 41

D = f"$3:$3002"
NRNG = lambda col: f"NOVEDADES!${col}${NOV_R0}:${col}${NOV_R1}"
DRNG = lambda col: f"DESPACHOS!${col}${DESP_R0}:${col}${DESP_R1}"
LRNG = lambda col: f"LISTAS!${col}${LST_R0}:${col}${LST_R1}"

# ---------- PALETA (misma del archivo actual) ----------
VERDE   = "FF1F4E2E"   # marca / titulos
AZUL    = "FF2E75B6"   # encabezado de columna CALCULADA
ORO     = "FFBF8F00"   # encabezado de columna MANUAL
AMAR    = "FFFFF2CC"   # celda manual
GRIS    = "FFF2F2F2"   # celda calculada
GRIS_OS = "FFD9D9D9"
BLANCO  = "FFFFFFFF"
ROJO_F  = "FFFFC7CE"; ROJO_T  = "FF9C0006"
AMB_F   = "FFFFEB9C"; AMB_T   = "FF9C6500"
VERD_F  = "FFC6EFCE"; VERD_T  = "FF006100"
AZUL_F  = "FFDDEBF7"

F9   = Font(name="Arial", size=9)
F9B  = Font(name="Arial", size=9, bold=True)
FHDR = Font(name="Arial", size=9, bold=True, color=BLANCO)
FTIT = Font(name="Arial", size=14, bold=True, color=BLANCO)
FSEC = Font(name="Arial", size=10, bold=True, color=BLANCO)
FKPI = Font(name="Arial", size=18, bold=True, color=VERDE)
FKPL = Font(name="Arial", size=8, bold=True, color=BLANCO)
FNOTA= Font(name="Arial", size=8, italic=True, color="FF595959")

fill = lambda c: PatternFill("solid", fgColor=c)
BORDE = Border(*[Side(style="thin", color="FFBFBFBF")]*4)
CEN = Alignment(horizontal="center", vertical="center", wrap_text=True)
IZQ = Alignment(horizontal="left",   vertical="center")
IZQW= Alignment(horizontal="left",   vertical="center", wrap_text=True)

FMT_FECHA = "dd/mm/yyyy"; FMT_MON = '"$"#,##0'; FMT_NUM = "#,##0"; FMT_PCT = "0.0%"; FMT_D1 = "#,##0.0"

wb = openpyxl.Workbook()
wb.remove(wb.active)

def hoja(nombre, color_tab):
    ws = wb.create_sheet(nombre)
    ws.sheet_properties.tabColor = color_tab
    ws.sheet_view.showGridLines = False
    return ws

def titulo(ws, celda, texto, ancho_merge, alto=26):
    ws[celda] = texto; ws[celda].font = FTIT; ws[celda].fill = fill(VERDE)
    ws[celda].alignment = IZQ
    col = openpyxl.utils.cell.coordinate_from_string(celda)[0]
    row = openpyxl.utils.cell.coordinate_from_string(celda)[1]
    c0 = openpyxl.utils.column_index_from_string(col)
    ws.merge_cells(start_row=row, start_column=c0, end_row=row, end_column=c0+ancho_merge-1)
    ws.row_dimensions[row].height = alto

def seccion(ws, row, col0, ncols, texto):
    c = ws.cell(row=row, column=col0, value=texto)
    c.font = FSEC; c.fill = fill(VERDE); c.alignment = IZQ
    ws.merge_cells(start_row=row, start_column=col0, end_row=row, end_column=col0+ncols-1)
    ws.row_dimensions[row].height = 18

# =====================================================================
# HOJA LISTAS
# =====================================================================
ls = hoja("LISTAS", "FF808080")

TIPOS = [
    ("Avería / producto dañado en transporte", "Alta",  3),
    ("Devolución parcial",                      "Media", 3),
    ("Rechazo total del pedido",                "Alta",  2),
    ("Faltante en la entrega",                  "Alta",  2),
    ("Sobrante en la entrega",                  "Baja",  5),
    ("Producto equivocado",                     "Alta",  2),
    ("Producto vencido o próximo a vencer",     "Alta",  3),
    ("Empaque en mal estado",                   "Media", 3),
    ("Retraso en vía / entrega tardía",         "Alta",  1),
    ("Cliente cerrado / no ubicado",            "Media", 2),
    ("Cliente rechaza / no recibe",             "Media", 2),
    ("Dirección errada",                        "Media", 2),
    ("Vehículo varado / falla mecánica",        "Alta",  1),
    ("Cobro pendiente / flete no liquidado",    "Media", 5),
    ("Cumplido / soporte no entregado",         "Media", 4),
    ("Diferencia en facturación o precio",      "Media", 5),
]
CAUSAS = [
    ("Manipulación en cargue / descargue", "Transporte"),
    ("Estibado o embalaje deficiente",     "Bodega"),
    ("Error de alistamiento (picking)",    "Bodega"),
    ("Sobrecupo o mal acomodo en vehículo","Transporte"),
    ("Demora del transportador",           "Transporte"),
    ("Falla mecánica del vehículo",        "Transporte"),
    ("Ruta mal programada",                "Logística"),
    ("Error de digitación del pedido",     "Comercial"),
    ("Error en facturación",               "Facturación"),
    ("Dirección desactualizada en maestro","Comercial"),
    ("Cliente sin cupo / cartera bloqueada","Cartera"),
    ("Cliente no disponible / fuera de horario","Comercial"),
    ("Producto con baja rotación / vencido","Calidad"),
    ("Acuerdo comercial con el cliente",   "Comercial"),
    ("Tráfico, cierre vial u orden público","Externo"),
    ("Clima adverso",                      "Externo"),
    ("Sin causa asignada",                 "Por definir"),
]
ESTADOS = [
    ("Pendiente", "NO"), ("En gestión", "NO"), ("En tránsito (retorno)", "NO"),
    ("Recibida en bodega", "NO"), ("En inspección", "NO"),
    ("Escalada a transportadora", "NO"), ("Pendiente nota crédito", "NO"),
    ("Resuelto / Cerrado", "SÍ"), ("Cerrada sin costo", "SÍ"), ("Anulada", "SÍ"),
]
TRANSP = ["CG CARGA SAS", "GESTO AGRO S.A.S", "TACMO SAS", "GOLDEN"]
RESPON = ["BRAYAN", "COORD. LOGÍSTICA", "JEFE DE BODEGA", "ANALISTA DE TRANSPORTE",
          "FACTURACIÓN", "CARTERA", "COMERCIAL", "CALIDAD"]
ZONAS  = ["BOGOT","NORTE - SUR","CORABASTOS","SUBA","COTA","FUNZA","SOACHA","GACHANCIPA",
          "TOCANCIPA","CHIA","CAJICA","ZIPAQUIRA","MOSQUERA","MADRID","TENJO","TABIO",
          "SOPO","LA CALERA","FACATATIVA","SIBATE","SABAN"]

titulo(ls, "A1", "CATÁLOGOS Y REGLAS DE NEGOCIO — no borre encabezados, agregue filas hacia abajo", 19)
hdrs = [(1,"A","TIPO DE NOVEDAD"),(2,"B","CRITICIDAD"),(3,"C","SLA (días hábiles)"),
        (5,"E","CAUSA RAÍZ"),(6,"F","ÁREA RESPONSABLE"),
        (8,"H","ESTADO"),(9,"I","¿CIERRA? (SÍ/NO)"),
        (11,"K","TRANSPORTADORA"),(13,"M","RESPONSABLE"),
        (15,"O","ZONA CERCANA (SLA corto)"),(17,"Q","PLAZO ZONA CERCANA (días)"),(18,"R","PLAZO NACIONAL (días)")]
for ci, cl, tx in hdrs:
    c = ls.cell(row=2, column=ci, value=tx); c.font = FHDR; c.fill = fill(ORO); c.alignment = CEN; c.border = BORDE
ls.row_dimensions[2].height = 30

def vol(ws, col, row0, valores, fmt=None, fillc=AMAR):
    for i, v in enumerate(valores):
        c = ws.cell(row=row0+i, column=openpyxl.utils.column_index_from_string(col), value=v)
        c.font = F9; c.fill = fill(fillc); c.border = BORDE; c.alignment = IZQ
        if fmt: c.number_format = fmt; c.alignment = CEN

vol(ls,"A",3,[t[0] for t in TIPOS]);  vol(ls,"B",3,[t[1] for t in TIPOS]); vol(ls,"C",3,[t[2] for t in TIPOS], FMT_NUM)
vol(ls,"E",3,[c[0] for c in CAUSAS]); vol(ls,"F",3,[c[1] for c in CAUSAS])
vol(ls,"H",3,[e[0] for e in ESTADOS]);vol(ls,"I",3,[e[1] for e in ESTADOS])
vol(ls,"K",3,TRANSP); vol(ls,"M",3,RESPON); vol(ls,"O",3,ZONAS)
vol(ls,"Q",3,[2], FMT_NUM); vol(ls,"R",3,[5], FMT_NUM)

for col, w in {"A":38,"B":12,"C":11,"D":2,"E":36,"F":16,"G":2,"H":24,"I":14,"J":2,
               "K":24,"L":2,"M":24,"N":2,"O":26,"P":2,"Q":13,"R":13}.items():
    ls.column_dimensions[col].width = w
ls.freeze_panes = "A3"

# LISTAS: los catalogos arrancan en la fila 3 (1=titulo, 2=encabezado)
LST0, LST1 = 3, 42
L_TIPO, L_CRIT, L_SLA = f"LISTAS!$A${LST0}:$A${LST1}", f"LISTAS!$B${LST0}:$B${LST1}", f"LISTAS!$C${LST0}:$C${LST1}"
L_CAUS, L_AREA        = f"LISTAS!$E${LST0}:$E${LST1}", f"LISTAS!$F${LST0}:$F${LST1}"
L_EST,  L_CIER        = f"LISTAS!$H${LST0}:$H${LST1}", f"LISTAS!$I${LST0}:$I${LST1}"
L_TRAN, L_RESP, L_ZON = f"LISTAS!$K${LST0}:$K${LST1}", f"LISTAS!$M${LST0}:$M${LST1}", f"LISTAS!$O${LST0}:$O${LST1}"

# =====================================================================
# HOJA DESPACHOS (BASE)
# =====================================================================
ds = hoja("DESPACHOS", VERDE)
titulo(ds, "A1", "DESPACHOS / BASE — pegue aquí el export de Access desde la fila 3 (columnas A a J). K, L y M se digitan; N y O se calculan solas.", 15)

DESP_COLS = [
 ("A","# Planilla",            10, "M", "General"),
 ("B","# Pedido / Remisión",   14, "M", "General"),
 ("C","# Factura",             11, "M", "General"),
 ("D","Cliente",               34, "M", "General"),
 ("E","Peso KG",               10, "M", FMT_D1),
 ("F","Transportadora",        20, "M", "General"),
 ("G","Transportador",         26, "M", "General"),
 ("H","Placa",                 10, "M", "General"),
 ("I","Ruta",                  20, "M", "General"),
 ("J","Fecha despacho",        14, "M", FMT_FECHA),
 ("K","Destino / Ciudad",      20, "M", "General"),
 ("L","Cajas enviadas",        13, "M", FMT_NUM),
 ("M","Valor despachado",      16, "M", FMT_MON),
 ("N","Zona SLA",              12, "C", "General"),
 ("O","¿Tiene novedad?",       15, "C", "General"),
]
for col, tx, w, tipo, fmt in DESP_COLS:
    c = ds[f"{col}2"]; c.value = tx; c.font = FHDR
    c.fill = fill(ORO if tipo == "M" else AZUL); c.alignment = CEN; c.border = BORDE
    ds.column_dimensions[col].width = w
ds.row_dimensions[2].height = 30

F_ZONA = ('=IF($B{r}="","",IF(SUMPRODUCT(({Z}<>"")*ISNUMBER(SEARCH({Z},$I{r}&" "&$K{r})))>0,'
          '"CERCANA","NACIONAL"))')
F_TIENE= ('=IF($B{r}="","",IF(COUNTIFS({NC},$B{r})=0,"—","SÍ ("&COUNTIFS({NC},$B{r})&")"))')

for r in range(DESP_R0, DESP_R1+1):
    for col, tx, w, tipo, fmt in DESP_COLS:
        c = ds[f"{col}{r}"]
        c.font = F9; c.border = BORDE; c.number_format = fmt
        if tipo == "M":
            c.fill = fill(AMAR); c.protection = Protection(locked=False)
        else:
            c.fill = fill(GRIS); c.alignment = CEN
    ds[f"N{r}"] = F_ZONA.format(r=r, Z=L_ZON)
    ds[f"O{r}"] = F_TIENE.format(r=r, NC=NRNG("C"))
ds.freeze_panes = "C3"
ds.auto_filter.ref = f"A2:O{DESP_R1}"

# =====================================================================
# HOJA NOVEDADES
# =====================================================================
nv = hoja("NOVEDADES", "FFBF8F00")
titulo(nv, "A1", "MATRIZ DE NOVEDADES DE LOGÍSTICA Y TRANSPORTE — GESTOAGRO S.A.S.", 28)
nv["A2"] = ("Digite SOLO las celdas AMARILLAS. La llave es el # Pedido / Remisión (columna C): al escribirlo se traen "
            "cliente, destino, ruta, transportadora, transportador, placa y fecha de despacho. Las celdas GRISES no se tocan.")
nv["A2"].font = FNOTA; nv["A2"].alignment = IZQ
nv.merge_cells("A2:AB2"); nv.row_dimensions[2].height = 16

NOV_COLS = [
 ("A","Consecutivo",            11,"C","General"),
 ("B","Fecha novedad",          13,"M",FMT_FECHA),
 ("C","# Pedido / Remisión",    15,"M","General"),
 ("D","Cliente",                32,"C","General"),
 ("E","Destino / Ciudad",       18,"C","General"),
 ("F","Ruta",                   18,"C","General"),
 ("G","Transportadora",         20,"C","General"),
 ("H","Transportador",          24,"C","General"),
 ("I","Placa",                  10,"C","General"),
 ("J","Fecha despacho",         13,"C",FMT_FECHA),
 ("K","Verif. despacho",        14,"C","General"),
 ("L","Tipo de novedad",        34,"M","General"),
 ("M","Causa raíz",             34,"M","General"),
 ("N","Área responsable",       16,"C","General"),
 ("O","Responsable",            20,"M","General"),
 ("P","Criticidad",             11,"C","General"),
 ("Q","Cajas afectadas",        13,"M",FMT_NUM),
 ("R","Valor afectado",         15,"M",FMT_MON),
 ("S","% del despacho",         13,"C",FMT_PCT),
 ("T","Estado",                 22,"M","General"),
 ("U","Fecha compromiso",       15,"C",FMT_FECHA),
 ("V","Fecha cierre real",      15,"M",FMT_FECHA),
 ("W","Días de gestión",        13,"C",FMT_NUM),
 ("X","Días de mora",           12,"C",FMT_NUM),
 ("Y","Semáforo SLA",           20,"C","General"),
 ("Z","Acción correctiva",      38,"M","General"),
 ("AA","Observaciones",         38,"M","General"),
 ("AB","Soporte / evidencia",   26,"M","General"),
]
for col, tx, w, tipo, fmt in NOV_COLS:
    c = nv[f"{col}3"]; c.value = tx; c.font = FHDR
    c.fill = fill(ORO if tipo == "M" else AZUL); c.alignment = CEN; c.border = BORDE
    nv.column_dimensions[col].width = w
nv.row_dimensions[3].height = 32

BX = lambda col, r: f"${col}{r}"
FRM = {
 "A": '=IF($C{r}="","","NOV-"&TEXT(ROW()-3,"0000"))',
 "D": '=IF($C{r}="","",IFERROR(INDEX({dD},MATCH($C{r},{dB},0)),"SIN DESPACHO"))',
 "E": '=IF($C{r}="","",IFERROR(INDEX({dK},MATCH($C{r},{dB},0)),""))',
 "F": '=IF($C{r}="","",IFERROR(INDEX({dI},MATCH($C{r},{dB},0)),""))',
 "G": '=IF($C{r}="","",IFERROR(INDEX({dF},MATCH($C{r},{dB},0)),""))',
 "H": '=IF($C{r}="","",IFERROR(INDEX({dG},MATCH($C{r},{dB},0)),""))',
 "I": '=IF($C{r}="","",IFERROR(INDEX({dH},MATCH($C{r},{dB},0)),""))',
 "J": '=IF($C{r}="","",IFERROR(INDEX({dJ},MATCH($C{r},{dB},0)),""))',
 "K": '=IF($C{r}="","",IF(COUNTIFS({dB},$C{r})=0,"NO EXISTE",IF(COUNTIFS({dB},$C{r})>1,"DUPLICADO","OK")))',
 "N": '=IF($M{r}="","",IFERROR(INDEX({lAREA},MATCH($M{r},{lCAUS},0)),"Por definir"))',
 "P": '=IF($L{r}="","",IFERROR(INDEX({lCRIT},MATCH($L{r},{lTIPO},0)),"Media"))',
 "S": '=IFERROR(IF(OR($R{r}="",$C{r}=""),"",$R{r}/INDEX({dM},MATCH($C{r},{dB},0))),"")',
 "U": '=IF(OR($B{r}="",$L{r}=""),"",WORKDAY($B{r},IFERROR(INDEX({lSLA},MATCH($L{r},{lTIPO},0)),3)))',
 "W": '=IF($B{r}="","",IF($V{r}<>"",$V{r}-$B{r},TODAY()-$B{r}))',
 "X": '=IF(OR($B{r}="",$U{r}=""),"",IF($V{r}<>"",MAX(0,$V{r}-$U{r}),MAX(0,TODAY()-$U{r})))',
 "Y": ('=IF($C{r}="","",IF(IFERROR(INDEX({lCIER},MATCH($T{r},{lEST},0)),"NO")="SÍ",'
       'IF(N($X{r})>0,"CERRADA FUERA DE SLA","CERRADA EN SLA"),'
       'IF($U{r}="","SIN CLASIFICAR",IF(N($X{r})>0,"VENCIDA",IF(TODAY()>=$U{r}-1,"POR VENCER","EN PLAZO")))))'),
}
ARGS = dict(dB=DRNG("B"), dD=DRNG("D"), dF=DRNG("F"), dG=DRNG("G"), dH=DRNG("H"),
            dI=DRNG("I"), dJ=DRNG("J"), dK=DRNG("K"), dM=DRNG("M"),
            lTIPO=L_TIPO, lCRIT=L_CRIT, lSLA=L_SLA, lCAUS=L_CAUS, lAREA=L_AREA,
            lEST=L_EST, lCIER=L_CIER)

for r in range(NOV_R0, NOV_R1+1):
    for col, tx, w, tipo, fmt in NOV_COLS:
        c = nv[f"{col}{r}"]
        c.font = F9; c.border = BORDE; c.number_format = fmt
        if tipo == "M":
            c.fill = fill(AMAR); c.protection = Protection(locked=False)
        else:
            c.fill = fill(GRIS)
        if col in ("A","B","I","J","K","P","Q","S","U","V","W","X","Y"):
            c.alignment = CEN
    for col, f in FRM.items():
        nv[f"{col}{r}"] = f.format(r=r, **ARGS)
nv.freeze_panes = "D4"
nv.auto_filter.ref = f"A3:AB{NOV_R1}"

# =====================================================================
# HOJA DASHBOARD
# =====================================================================
db = hoja("DASHBOARD", VERDE)
for col, w in {"A":2,"B":36,"C":13,"D":13,"E":15,"F":11,"G":11,"H":11,"I":11,"J":11,
               "K":16,"L":2,"M":2,"N":22,"O":20,"P":2}.items():
    db.column_dimensions[col].width = w

db["B2"] = "DASHBOARD DE NOVEDADES DE LOGÍSTICA Y TRANSPORTE — GESTOAGRO S.A.S."
db["B2"].font = Font(name="Arial", size=16, bold=True, color=VERDE); db.merge_cells("B2:K2")
db.row_dimensions[2].height = 24
db["B3"] = ("Todos los indicadores respetan el PERIODO de abajo. Novedades se filtran por Fecha novedad; "
            "despachos por Fecha despacho.")
db["B3"].font = FNOTA; db.merge_cells("B3:K3")

db["B4"] = "📅 PERIODO A CONSULTAR"; db["B4"].font = FSEC; db["B4"].fill = fill(VERDE); db["B4"].alignment = IZQ
db.merge_cells("B4:C4")
for coord, txt in [("D4","Desde:"), ("F4","Hasta:")]:
    db[coord] = txt; db[coord].font = F9B; db[coord].alignment = Alignment(horizontal="right", vertical="center")
import datetime
for coord, val in [("E4", datetime.date(2026,1,1)), ("G4", datetime.date(2026,12,31))]:
    c = db[coord]; c.value = val; c.font = Font(name="Arial", size=10, bold=True, color=VERDE)
    c.fill = fill(AMAR); c.number_format = FMT_FECHA; c.alignment = CEN; c.border = BORDE
    c.protection = Protection(locked=False)
db["H4"] = "◄ Cambie las dos fechas AMARILLAS y todo el tablero se recalcula."
db["H4"].font = FNOTA; db.merge_cells("H4:K4"); db.row_dimensions[4].height = 20

PER_N = f'{NRNG("B")},">="&$E$4,{NRNG("B")},"<="&$G$4'
PER_D = f'{DRNG("J")},">="&$E$4,{DRNG("J")},"<="&$G$4'
nB,nC,nG,nL,nM,nQ,nR,nT,nW,nY = (NRNG(x) for x in ["B","C","G","L","M","Q","R","T","W","Y"])
dB,dC,dD,dF,dH,dJ,dK,dM,dO = (DRNG(x) for x in ["B","C","D","F","H","J","K","M","O"])
ABIERTA = lambda extra="": ("+".join(
    f'COUNTIFS({nY},"{s}",{PER_N}{extra})' for s in ["EN PLAZO","POR VENCER","VENCIDA","SIN CLASIFICAR"]))

KPIS = [
 (6, "B", "NOVEDADES DEL PERIODO",      f'=COUNTIFS({PER_N})',                                   FMT_NUM),
 (6, "D", "PEDIDOS DESPACHADOS",        f'=COUNTIFS({PER_D})',                                   FMT_NUM),
 (6, "F", "% RATIO DE INCIDENCIA",      f'=IFERROR(COUNTIFS({PER_D},{dO},"SÍ*")/COUNTIFS({PER_D}),0)', FMT_PCT),
 (6, "H", "NOVEDADES ABIERTAS",         "=" + ABIERTA(),                                         FMT_NUM),
 (6, "J", "NOVEDADES CERRADAS",         f'=COUNTIFS({nY},"CERRADA*",{PER_N})',                   FMT_NUM),
 (9, "B", "VALOR IMPACTADO",            f'=SUMIFS({nR},{PER_N})',                                FMT_MON),
 (9, "D", "CAJAS AFECTADAS",            f'=SUMIFS({nQ},{PER_N})',                                FMT_NUM),
 (9, "F", "DÍAS PROM. DE GESTIÓN",      f'=IFERROR(ROUND(AVERAGEIFS({nW},{PER_N}),1),0)',        FMT_D1),
 (9, "H", "VENCIDAS (SLA roto)",        f'=COUNTIFS({nY},"VENCIDA",{PER_N})',                    FMT_NUM),
 (9, "J", "% CUMPLIMIENTO SLA",         f'=IFERROR(COUNTIFS({nY},"CERRADA EN SLA",{PER_N})/COUNTIFS({nY},"CERRADA*",{PER_N}),"—")', FMT_PCT),
]
for row, col, lbl, frm, fmt in KPIS:
    ci = openpyxl.utils.column_index_from_string(col)
    c = db.cell(row=row, column=ci, value=lbl); c.font = FKPL; c.fill = fill(VERDE); c.alignment = CEN
    db.merge_cells(start_row=row, start_column=ci, end_row=row, end_column=ci+1)
    v = db.cell(row=row+1, column=ci, value=frm); v.font = FKPI; v.fill = fill(GRIS)
    v.alignment = CEN; v.number_format = fmt; v.border = BORDE
    db.merge_cells(start_row=row+1, start_column=ci, end_row=row+1, end_column=ci+1)
    db.row_dimensions[row].height = 22; db.row_dimensions[row+1].height = 30

def tabla_hdr(row, cols):
    for col, tx in cols:
        c = db[f"{col}{row}"]; c.value = tx; c.font = FHDR; c.fill = fill(AZUL)
        c.alignment = CEN; c.border = BORDE
    db.row_dimensions[row].height = 28

def celda(coord, valor, fmt="General", neg=False, bold=False, al=None):
    c = db[coord]; c.value = valor; c.number_format = fmt; c.border = BORDE
    c.font = F9B if bold else F9; c.fill = fill(GRIS_OS if bold else GRIS)
    c.alignment = al or CEN
    return c

# ---- 1. CAUSA RAIZ ----
seccion(db, 12, 2, 5, "1. CAUSA RAÍZ — CONTEO, PARTICIPACIÓN E IMPACTO ECONÓMICO")
tabla_hdr(13, [("B","Causa raíz"),("C","# Novedades"),("D","% Participación"),("E","Valor impactado"),("F","Orden")])
for r in range(14, 31):
    lr = r - 11
    celda(f"B{r}", f'=IF(LISTAS!$E{lr}="","",LISTAS!$E{lr})', al=IZQ)
    celda(f"C{r}", f'=IF($B{r}="","",COUNTIFS({nM},$B{r},{PER_N}))', FMT_NUM)
    celda(f"D{r}", f'=IF($B{r}="","",IFERROR($C{r}/$C$31,0))', FMT_PCT)
    celda(f"E{r}", f'=IF($B{r}="","",SUMIFS({nR},{nM},$B{r},{PER_N}))', FMT_MON)
    celda(f"F{r}", f'=IF($B{r}="","",$C{r}+ROW()/100000)', "0.00000")
celda("B31", "TOTAL", bold=True, al=IZQ); celda("C31", "=SUM($C$14:$C$30)", FMT_NUM, bold=True)
celda("D31", '=IF($C$31=0,0,1)', FMT_PCT, bold=True); celda("E31", "=SUM($E$14:$E$30)", FMT_MON, bold=True)
celda("F31", "", bold=True)
db["F13"].value = "Orden (auxiliar)"

# ---- 2. TOP 5 ----
seccion(db, 33, 2, 4, "2. TOP 5 CAUSAS RAÍZ — ranking automático del periodo")
tabla_hdr(34, [("B","Puesto"),("C","Causa raíz"),("D","# Novedades"),("E","% Participación")])
for r in range(35, 40):
    k = r - 34
    celda(f"B{r}", f'="#"&{k}', bold=True)
    celda(f"C{r}", f'=IFERROR(INDEX($B$14:$B$30,MATCH(LARGE($F$14:$F$30,{k}),$F$14:$F$30,0)),"—")', al=IZQ)
    celda(f"D{r}", f'=IFERROR(INDEX($C$14:$C$30,MATCH(LARGE($F$14:$F$30,{k}),$F$14:$F$30,0)),0)', FMT_NUM)
    celda(f"E{r}", f'=IFERROR($D{r}/$C$31,0)', FMT_PCT)

# ---- 3. TIPO DE NOVEDAD ----
seccion(db, 41, 2, 7, "3. NOVEDADES POR TIPO — volumen, impacto y estado de gestión")
tabla_hdr(42, [("B","Tipo de novedad"),("C","# Novedades"),("D","% Part."),("E","Valor impactado"),
               ("F","Abiertas"),("G","Cerradas"),("H","Vencidas")])
for r in range(43, 59):
    lr = r - 40
    celda(f"B{r}", f'=IF(LISTAS!$A{lr}="","",LISTAS!$A{lr})', al=IZQ)
    celda(f"C{r}", f'=IF($B{r}="","",COUNTIFS({nL},$B{r},{PER_N}))', FMT_NUM)
    celda(f"D{r}", f'=IF($B{r}="","",IFERROR($C{r}/$C$59,0))', FMT_PCT)
    celda(f"E{r}", f'=IF($B{r}="","",SUMIFS({nR},{nL},$B{r},{PER_N}))', FMT_MON)
    celda(f"F{r}", f'=IF($B{r}="","",{ABIERTA(f",{nL},$B{r}")})', FMT_NUM)
    celda(f"G{r}", f'=IF($B{r}="","",COUNTIFS({nL},$B{r},{nY},"CERRADA*",{PER_N}))', FMT_NUM)
    celda(f"H{r}", f'=IF($B{r}="","",COUNTIFS({nL},$B{r},{nY},"VENCIDA",{PER_N}))', FMT_NUM)
celda("B59","TOTAL",bold=True,al=IZQ)
for col in "CEFGH": celda(f"{col}59", f"=SUM(${col}$43:${col}$58)", FMT_MON if col=="E" else FMT_NUM, bold=True)
celda("D59", '=IF($C$59=0,0,1)', FMT_PCT, bold=True)

# ---- 4. TRANSPORTADORA ----
seccion(db, 61, 2, 10, "4. NOVEDADES ABIERTAS VS. CERRADAS POR TRANSPORTADORA")
tabla_hdr(62, [("B","Transportadora"),("C","Despachos"),("D","Novedades"),("E","% Incidencia"),
               ("F","Abiertas"),("G","Vencidas"),("H","Cerradas"),("I","% Cierre"),
               ("J","Días prom."),("K","Valor impactado")])
for r in range(63, 73):
    lr = r - 60
    celda(f"B{r}", f'=IF(LISTAS!$K{lr}="","",LISTAS!$K{lr})', al=IZQ)
    celda(f"C{r}", f'=IF($B{r}="","",COUNTIFS({dF},$B{r},{PER_D}))', FMT_NUM)
    celda(f"D{r}", f'=IF($B{r}="","",COUNTIFS({nG},$B{r},{PER_N}))', FMT_NUM)
    celda(f"E{r}", f'=IF($B{r}="","",IFERROR($D{r}/$C{r},"—"))', FMT_PCT)
    celda(f"F{r}", f'=IF($B{r}="","",{ABIERTA(f",{nG},$B{r}")})', FMT_NUM)
    celda(f"G{r}", f'=IF($B{r}="","",COUNTIFS({nG},$B{r},{nY},"VENCIDA",{PER_N}))', FMT_NUM)
    celda(f"H{r}", f'=IF($B{r}="","",COUNTIFS({nG},$B{r},{nY},"CERRADA*",{PER_N}))', FMT_NUM)
    celda(f"I{r}", f'=IF($B{r}="","",IFERROR($H{r}/$D{r},"—"))', FMT_PCT)
    celda(f"J{r}", f'=IF($B{r}="","",IFERROR(ROUND(AVERAGEIFS({nW},{nG},$B{r},{PER_N}),1),0))', FMT_D1)
    celda(f"K{r}", f'=IF($B{r}="","",SUMIFS({nR},{nG},$B{r},{PER_N}))', FMT_MON)
celda("B73","TOTAL",bold=True,al=IZQ)
for col in "CDFGHK": celda(f"{col}73", f"=SUM(${col}$63:${col}$72)", FMT_MON if col=="K" else FMT_NUM, bold=True)
celda("E73", '=IFERROR($D$73/$C$73,"—")', FMT_PCT, bold=True)
celda("I73", '=IFERROR($H$73/$D$73,"—")', FMT_PCT, bold=True)
celda("J73", f'=IFERROR(ROUND(AVERAGEIFS({nW},{PER_N}),1),0)', FMT_D1, bold=True)

# ---- 5. ESTADO ----
seccion(db, 75, 2, 4, "5. NOVEDADES POR ESTADO — pipeline de gestión")
tabla_hdr(76, [("B","Estado"),("C","# Casos"),("D","% Part."),("E","Valor impactado")])
for r in range(77, 87):
    lr = r - 74
    celda(f"B{r}", f'=IF(LISTAS!$H{lr}="","",LISTAS!$H{lr})', al=IZQ)
    celda(f"C{r}", f'=IF($B{r}="","",COUNTIFS({nT},$B{r},{PER_N}))', FMT_NUM)
    celda(f"D{r}", f'=IF($B{r}="","",IFERROR($C{r}/$C$87,0))', FMT_PCT)
    celda(f"E{r}", f'=IF($B{r}="","",SUMIFS({nR},{nT},$B{r},{PER_N}))', FMT_MON)
celda("B87","TOTAL",bold=True,al=IZQ); celda("C87","=SUM($C$77:$C$86)",FMT_NUM,bold=True)
celda("D87",'=IF($C$87=0,0,1)',FMT_PCT,bold=True); celda("E87","=SUM($E$77:$E$86)",FMT_MON,bold=True)

# ---- CONSULTA RAPIDA ----
seccion(db, 12, 14, 2, "CONSULTA RÁPIDA DE PEDIDO")
db["N13"] = "Digite # Pedido →"; db["N13"].font = F9B; db["N13"].alignment = IZQ; db["N13"].border = BORDE
c = db["O13"]; c.fill = fill(AMAR); c.font = Font(name="Arial", size=11, bold=True, color=VERDE)
c.alignment = CEN; c.border = BORDE; c.protection = Protection(locked=False)
CONSULTA = [
 ("N14","Cliente",           f'=IF($O$13="","—",IFERROR(INDEX({dD},MATCH($O$13,{dB},0)),"NO EXISTE"))', "General"),
 ("N15","# Factura",         f'=IF($O$13="","—",IFERROR(INDEX({dC},MATCH($O$13,{dB},0)),"—"))', "General"),
 ("N16","Destino / Ciudad",  f'=IF($O$13="","—",IFERROR(INDEX({dK},MATCH($O$13,{dB},0)),"—"))', "General"),
 ("N17","Transportadora",    f'=IF($O$13="","—",IFERROR(INDEX({dF},MATCH($O$13,{dB},0)),"—"))', "General"),
 ("N18","Placa",             f'=IF($O$13="","—",IFERROR(INDEX({dH},MATCH($O$13,{dB},0)),"—"))', "General"),
 ("N19","Fecha despacho",    f'=IF($O$13="","—",IFERROR(INDEX({dJ},MATCH($O$13,{dB},0)),"—"))', FMT_FECHA),
 ("N20","Novedades del pedido", f'=IF($O$13="","—",COUNTIFS({nC},$O$13))', FMT_NUM),
 ("N21","Valor afectado",    f'=IF($O$13="","—",SUMIFS({nR},{nC},$O$13))', FMT_MON),
 ("N22","Estado más reciente",f'=IF($O$13="","—",IFERROR(LOOKUP(2,1/({nC}=$O$13),{nT}),"—"))', "General"),
 ("N23","Semáforo SLA",      f'=IF($O$13="","—",IFERROR(LOOKUP(2,1/({nC}=$O$13),{nY}),"—"))', "General"),
]
for coord, lbl, frm, fmt in CONSULTA:
    r = int(coord[1:])
    db[coord] = lbl; db[coord].font = F9; db[coord].alignment = IZQ; db[coord].border = BORDE
    v = db[f"O{r}"]; v.value = frm; v.font = F9B; v.fill = fill(GRIS); v.number_format = fmt
    v.alignment = CEN; v.border = BORDE
db["N25"] = "El semáforo y el estado corresponden a la novedad más reciente registrada para ese pedido."
db["N25"].font = FNOTA; db.merge_cells("N25:O27"); db["N25"].alignment = IZQW

# =====================================================================
# NOMBRES DEFINIDOS (listas dinamicas: crecen solas al agregar filas)
# =====================================================================
NOMBRES = {
 "TIPOS_NOVEDAD":  f"OFFSET(LISTAS!$A${LST0},0,0,MAX(1,COUNTA(LISTAS!$A${LST0}:$A${LST1})),1)",
 "CAUSAS_RAIZ":    f"OFFSET(LISTAS!$E${LST0},0,0,MAX(1,COUNTA(LISTAS!$E${LST0}:$E${LST1})),1)",
 "ESTADOS_NOV":    f"OFFSET(LISTAS!$H${LST0},0,0,MAX(1,COUNTA(LISTAS!$H${LST0}:$H${LST1})),1)",
 "TRANSPORTADORAS":f"OFFSET(LISTAS!$K${LST0},0,0,MAX(1,COUNTA(LISTAS!$K${LST0}:$K${LST1})),1)",
 "RESPONSABLES":   f"OFFSET(LISTAS!$M${LST0},0,0,MAX(1,COUNTA(LISTAS!$M${LST0}:$M${LST1})),1)",
}
for n, f in NOMBRES.items():
    wb.defined_names.add(DefinedName(n, attr_text=f))

def dv(ws, rango, **kw):
    d = DataValidation(**kw); ws.add_data_validation(d); d.add(rango); return d

# ---- Validaciones NOVEDADES ----
dv(nv, f"L{NOV_R0}:L{NOV_R1}", type="list", formula1="TIPOS_NOVEDAD", allow_blank=True,
   showErrorMessage=True, errorTitle="Tipo no válido",
   error="Elija un tipo de la lista. Para agregar uno nuevo vaya a LISTAS columna A.",
   promptTitle="Tipo de novedad", prompt="Elija de la lista. Define la criticidad y el SLA.", showInputMessage=True)
dv(nv, f"M{NOV_R0}:M{NOV_R1}", type="list", formula1="CAUSAS_RAIZ", allow_blank=True,
   showErrorMessage=True, errorTitle="Causa no válida",
   error="Elija una causa de la lista. Para agregar una nueva vaya a LISTAS columna E.",
   promptTitle="Causa raíz", prompt="Por qué ocurrió. Define el área responsable.", showInputMessage=True)
dv(nv, f"O{NOV_R0}:O{NOV_R1}", type="list", formula1="RESPONSABLES", allow_blank=True,
   showErrorMessage=True, errorTitle="Responsable no válido", error="Elija de la lista (LISTAS columna M).")
dv(nv, f"T{NOV_R0}:T{NOV_R1}", type="list", formula1="ESTADOS_NOV", allow_blank=True,
   showErrorMessage=True, errorTitle="Estado no válido",
   error="Elija un estado de la lista. Para agregar uno nuevo vaya a LISTAS columna H.",
   promptTitle="Estado", prompt="Los estados marcados ¿CIERRA?=SÍ cierran el caso y detienen el conteo de días.",
   showInputMessage=True)
dv(nv, f"B{NOV_R0}:B{NOV_R1}", type="date", operator="between",
   formula1="DATE(2020,1,1)", formula2="DATE(2035,12,31)", allow_blank=True,
   showErrorMessage=True, errorTitle="Fecha no válida", error="Escriba una fecha real (dd/mm/aaaa).")
dv(nv, f"V{NOV_R0}:V{NOV_R1}", type="custom", formula1=f'OR($V{NOV_R0}="",AND(ISNUMBER($V{NOV_R0}),$V{NOV_R0}>=$B{NOV_R0}))',
   allow_blank=True, showErrorMessage=True, errorTitle="Fecha de cierre inválida",
   error="La fecha de cierre no puede ser anterior a la fecha de la novedad.")
dv(nv, f"Q{NOV_R0}:Q{NOV_R1}", type="decimal", operator="greaterThanOrEqual", formula1="0",
   allow_blank=True, showErrorMessage=True, errorTitle="Cantidad inválida", error="Debe ser un número mayor o igual a 0.")
dv(nv, f"R{NOV_R0}:R{NOV_R1}", type="decimal", operator="greaterThanOrEqual", formula1="0",
   allow_blank=True, showErrorMessage=True, errorTitle="Valor inválido", error="Debe ser un número mayor o igual a 0.")

# ---- Validaciones DESPACHOS (aviso, no bloqueo: la hoja se pega desde Access) ----
d1 = dv(ds, f"F{DESP_R0}:F{DESP_R1}", type="list", formula1="TRANSPORTADORAS", allow_blank=True,
        showErrorMessage=True, errorTitle="Transportadora nueva",
        error="No está en LISTAS. Si es correcta, agréguela en LISTAS columna K para que entre al tablero.")
d1.errorStyle = "warning"
dv(ds, f"J{DESP_R0}:J{DESP_R1}", type="date", operator="between",
   formula1="DATE(2020,1,1)", formula2="DATE(2035,12,31)", allow_blank=True,
   showErrorMessage=True, errorTitle="Fecha no válida", error="Escriba una fecha real (dd/mm/aaaa)").errorStyle = "warning"
dv(ds, f"L{DESP_R0}:L{DESP_R1}", type="decimal", operator="greaterThanOrEqual", formula1="0", allow_blank=True)
dv(ds, f"M{DESP_R0}:M{DESP_R1}", type="decimal", operator="greaterThanOrEqual", formula1="0", allow_blank=True)

# =====================================================================
# FORMATO CONDICIONAL
# =====================================================================
def cf_txt(ws, rng, valor, bg, fg, bold=True):
    ws.conditional_formatting.add(rng, CellIsRule(
        operator="equal", formula=[f'"{valor}"'], fill=fill(bg),
        font=Font(name="Arial", size=9, bold=bold, color=fg)))

RNG = lambda c: f"{c}{NOV_R0}:{c}{NOV_R1}"
# 1) Semaforo SLA
for val, bg, fg in [("VENCIDA", ROJO_F, ROJO_T), ("POR VENCER", AMB_F, AMB_T),
                    ("EN PLAZO", VERD_F, VERD_T), ("CERRADA EN SLA", AZUL_F, "FF1F4E79"),
                    ("CERRADA FUERA DE SLA", "FFF8CBAD", "FF833C00"),
                    ("SIN CLASIFICAR", GRIS_OS, "FF595959")]:
    cf_txt(nv, RNG("Y"), val, bg, fg)
# 2) Criticidad
for val, bg, fg in [("Alta", ROJO_F, ROJO_T), ("Media", AMB_F, AMB_T), ("Baja", VERD_F, VERD_T)]:
    cf_txt(nv, RNG("P"), val, bg, fg)
# 3) Estado (data-driven con la columna ¿CIERRA? de LISTAS)
CIERRA = f'IFERROR(INDEX({L_CIER},MATCH($T{NOV_R0},{L_EST},0)),"NO")'
nv.conditional_formatting.add(RNG("T"), FormulaRule(
    formula=[f'$T{NOV_R0}="Pendiente"'], fill=fill(ROJO_F), font=Font(name="Arial", size=9, bold=True, color=ROJO_T)))
nv.conditional_formatting.add(RNG("T"), FormulaRule(
    formula=[f'AND($T{NOV_R0}<>"",{CIERRA}="SÍ")'], fill=fill(VERD_F), font=Font(name="Arial", size=9, bold=True, color=VERD_T)))
nv.conditional_formatting.add(RNG("T"), FormulaRule(
    formula=[f'AND($T{NOV_R0}<>"",{CIERRA}="NO")'], fill=fill(AMB_F), font=Font(name="Arial", size=9, bold=True, color=AMB_T)))
# 4) Verificacion de llave
nv.conditional_formatting.add(RNG("K"), FormulaRule(
    formula=[f'OR($K{NOV_R0}="NO EXISTE",$K{NOV_R0}="DUPLICADO")'],
    fill=fill(ROJO_F), font=Font(name="Arial", size=9, bold=True, color=ROJO_T)))
nv.conditional_formatting.add(RNG("K"), CellIsRule(
    operator="equal", formula=['"OK"'], font=Font(name="Arial", size=9, color=VERD_T)))
# 5) Dias de mora > 0
nv.conditional_formatting.add(RNG("X"), CellIsRule(
    operator="greaterThan", formula=["0"], fill=fill(ROJO_F), font=Font(name="Arial", size=9, bold=True, color=ROJO_T)))
# 6) Cerrada sin fecha de cierre
nv.conditional_formatting.add(RNG("V"), FormulaRule(
    formula=[f'AND($V{NOV_R0}="",LEFT($Y{NOV_R0},7)="CERRADA")'],
    fill=fill(ROJO_F), font=Font(name="Arial", size=9, bold=True, color=ROJO_T)))
# 7) Barra de datos sobre el valor afectado
nv.conditional_formatting.add(RNG("R"), DataBarRule(start_type="num", start_value=0,
    end_type="percentile", end_value=95, color="FFBF8F00", showValue=True, minLength=None, maxLength=None))
# 8) Resalte de fila completa cuando esta VENCIDA (solo tipografia: no tapa el codigo de colores)
nv.conditional_formatting.add(f"A{NOV_R0}:AB{NOV_R1}", FormulaRule(
    formula=[f'$Y{NOV_R0}="VENCIDA"'], font=Font(name="Arial", size=9, bold=True, color=ROJO_T)))

# DESPACHOS
ds.conditional_formatting.add(f"O{DESP_R0}:O{DESP_R1}", FormulaRule(
    formula=[f'LEFT($O{DESP_R0},2)="SÍ"'], fill=fill(AMB_F), font=Font(name="Arial", size=9, bold=True, color=AMB_T)))
ds.conditional_formatting.add(f"A{DESP_R0}:O{DESP_R1}", FormulaRule(
    formula=[f'AND($B{DESP_R0}<>"",COUNTIFS($B${DESP_R0}:$B${DESP_R1},$B{DESP_R0})>1)'],
    font=Font(name="Arial", size=9, bold=True, color="FF833C00")))

# DASHBOARD
db.conditional_formatting.add("F7", CellIsRule(operator="greaterThan", formula=["0.05"],
    fill=fill(ROJO_F), font=Font(name="Arial", size=18, bold=True, color=ROJO_T)))
db.conditional_formatting.add("F7", CellIsRule(operator="lessThanOrEqual", formula=["0.03"],
    fill=fill(VERD_F), font=Font(name="Arial", size=18, bold=True, color=VERD_T)))
db.conditional_formatting.add("H10", CellIsRule(operator="greaterThan", formula=["0"],
    fill=fill(ROJO_F), font=Font(name="Arial", size=18, bold=True, color=ROJO_T)))
db.conditional_formatting.add("H7", CellIsRule(operator="greaterThan", formula=["0"],
    fill=fill(AMB_F), font=Font(name="Arial", size=18, bold=True, color=AMB_T)))
db.conditional_formatting.add("J10", CellIsRule(operator="lessThan", formula=["0.9"],
    fill=fill(ROJO_F), font=Font(name="Arial", size=18, bold=True, color=ROJO_T)))
db.conditional_formatting.add("J10", CellIsRule(operator="greaterThanOrEqual", formula=["0.9"],
    fill=fill(VERD_F), font=Font(name="Arial", size=18, bold=True, color=VERD_T)))
db.conditional_formatting.add("C14:C30", DataBarRule(start_type="num", start_value=0,
    end_type="percentile", end_value=100, color="FF2E75B6", showValue=True))
db.conditional_formatting.add("C43:C58", DataBarRule(start_type="num", start_value=0,
    end_type="percentile", end_value=100, color="FF2E75B6", showValue=True))
db.conditional_formatting.add("E63:E72", CellIsRule(operator="greaterThan", formula=["0.05"],
    fill=fill(ROJO_F), font=Font(name="Arial", size=9, bold=True, color=ROJO_T)))
db.conditional_formatting.add("G63:G72", CellIsRule(operator="greaterThan", formula=["0"],
    fill=fill(ROJO_F), font=Font(name="Arial", size=9, bold=True, color=ROJO_T)))
db.conditional_formatting.add("I63:I72", CellIsRule(operator="lessThan", formula=["0.8"],
    fill=fill(AMB_F), font=Font(name="Arial", size=9, bold=True, color=AMB_T)))

# =====================================================================
# HOJA GUIA
# =====================================================================
gu = hoja("GUÍA", VERDE)
gu.column_dimensions["A"].width = 2
gu.column_dimensions["B"].width = 150
GUIA = [
 ("T", "GUÍA DE USO — MATRIZ DE NOVEDADES DE LOGÍSTICA Y TRANSPORTE · GESTOAGRO S.A.S."),
 ("H", "LA REGLA DE ORO — COLORES"),
 ("P", "•  Celdas AMARILLAS = usted las digita.        •  Celdas GRISES = se calculan solas, NO las toque.        •  Encabezado DORADO = columna de captura.        •  Encabezado AZUL = columna calculada."),
 ("H", "FLUJO DIARIO — PASO A PASO"),
 ("P", "1)  DESPACHOS: pegue el export de Access desde la fila 3 (columnas A a J, mismo orden). Luego complete a mano Destino/Ciudad (K), Cajas enviadas (L) y Valor despachado (M)."),
 ("P", "2)  NOVEDADES: para registrar un evento digite SOLO la Fecha novedad (B) y el # Pedido / Remisión (C). Cliente, destino, ruta, transportadora, transportador, placa y fecha de despacho se traen solos desde DESPACHOS."),
 ("P", "3)  Elija de las listas: Tipo de novedad (L), Causa raíz (M), Responsable (O) y Estado (T). El Área responsable, la Criticidad y la Fecha compromiso se calculan solas."),
 ("P", "4)  Registre el impacto: Cajas afectadas (Q) y Valor afectado (R). El % del despacho sale solo."),
 ("P", "5)  Al resolver el caso: cambie el Estado (T) a uno que cierre y escriba la Fecha cierre real (V). El semáforo pasa a CERRADA EN SLA o CERRADA FUERA DE SLA."),
 ("H", "CÓMO LEER EL SEMÁFORO SLA (columna Y)"),
 ("P", "EN PLAZO = dentro de la fecha compromiso.   POR VENCER = vence hoy o mañana.   VENCIDA = ya pasó la fecha compromiso y sigue abierta.   CERRADA EN SLA = se resolvió a tiempo.   CERRADA FUERA DE SLA = se resolvió tarde.   SIN CLASIFICAR = falta el Tipo de novedad."),
 ("H", "VERIFICACIÓN DE LA LLAVE (columna K)"),
 ("P", "OK = el pedido existe una sola vez en DESPACHOS.   NO EXISTE = el número está mal o el despacho no se ha pegado.   DUPLICADO = el pedido aparece más de una vez en DESPACHOS y el cruce puede traer el dato equivocado. Corrija antes de seguir."),
 ("H", "CÓMO CAMBIAR LAS REGLAS DE NEGOCIO"),
 ("P", "Todo se controla desde LISTAS, sin tocar fórmulas: A/B/C = tipo de novedad con su criticidad y su SLA en días hábiles;  E/F = causa raíz con su área responsable;  H/I = estados y cuáles cierran el caso;  K = transportadoras;  M = responsables;  O = zonas cercanas. Agregue filas hacia abajo: las listas desplegables crecen solas."),
 ("H", "DASHBOARD"),
 ("P", "Cambie las dos fechas amarillas del PERIODO y todo el tablero se recalcula: ratio de incidencia, top causas raíz, novedades por tipo, abiertas vs. cerradas por transportadora y pipeline por estado. La consulta rápida de la derecha trae la ficha completa de cualquier pedido."),
 ("H", "PROTECCIÓN — PIN 2026"),
 ("P", "DESPACHOS, NOVEDADES y DASHBOARD están protegidas para que nadie borre una fórmula; solo las celdas amarillas se editan. Para cambiar algo protegido: Revisar → Desproteger hoja → 2026. LISTAS queda libre para que pueda ampliar los catálogos."),
 ("H", "CAPACIDAD Y CIERRE"),
 ("P", "DESPACHOS admite 3.000 despachos y NOVEDADES 2.000 registros. Con su ciclo de ~1.000 pedidos cada 15 días, haga el cierre mensual: guarde una COPIA con el nombre del mes en una carpeta \"Históricos\", y en el archivo activo borre solo las celdas amarillas."),
 ("H", "SI USA GOOGLE SHEETS"),
 ("P", "Las fórmulas funcionan igual salvo dos: BUSCARX no existe (use ÍNDICE+COINCIDIR, que es lo que trae este archivo) y los nombres definidos no aceptan DESPLAZAMIENTO. En Sheets apunte la validación de datos directamente al rango, por ejemplo LISTAS!A3:A42."),
]
r = 2
for tipo, txt in GUIA:
    c = gu.cell(row=r, column=2, value=txt)
    if tipo == "T":
        c.font = FTIT; c.fill = fill(VERDE); gu.row_dimensions[r].height = 30
    elif tipo == "H":
        c.font = Font(name="Arial", size=10, bold=True, color=BLANCO); c.fill = fill(AZUL)
        gu.row_dimensions[r].height = 20
    else:
        c.font = Font(name="Arial", size=9); c.fill = fill(GRIS); gu.row_dimensions[r].height = 32
    c.alignment = IZQW
    r += 1

# =====================================================================
# PROTECCION, ORDEN Y GUARDADO
# =====================================================================
for ws in (ds, nv, db, gu):
    p = ws.protection
    p.password = "2026"; p.sheet = True; p.enable()
    p.autoFilter = False; p.sort = False; p.formatColumns = False; p.formatRows = False
    p.selectLockedCells = False; p.selectUnlockedCells = False

wb.move_sheet("GUÍA", offset=-wb.sheetnames.index("GUÍA"))
orden = ["GUÍA", "DASHBOARD", "NOVEDADES", "DESPACHOS", "LISTAS"]
wb._sheets = [wb[n] for n in orden]
wb.active = 1
wb.calculation.fullCalcOnLoad = True

import os
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "MATRIZ_NOVEDADES_LOGISTICA_GESTOAGRO.xlsx")
wb.save(OUT)
print("OK ->", OUT)
