# -*- coding: utf-8 -*-
"""Genera MATRIZ_NOVEDADES_..._EJEMPLO.xlsx: la misma matriz, ya con un mes
de datos ficticios cargados (novedades en ruta e internas), para ver el
tablero funcionando al abrirlo.

    python3 generar_matriz.py && python3 crear_ejemplo.py
"""
import os, shutil, datetime, warnings
import openpyxl
warnings.filterwarnings("ignore")

AQUI = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.join(AQUI, "MATRIZ_NOVEDADES_LOGISTICA_TRANSPORTE.xlsx")
DEST = os.path.join(AQUI, "MATRIZ_NOVEDADES_LOGISTICA_TRANSPORTE_EJEMPLO.xlsx")
shutil.copy(BASE, DEST)
D = datetime.date

# guia, fdesp, cliente, ciudad, transportadora, conductor, placa, und, valor, fpromesa, freal
ENVIOS = [
 # --- Transportadora A: cumple ---
 ("G-2401", "P-5001", D(2026,8,10), "Agroveterinaria El Roble",   "Bogotá",       "Transportadora A", "Juan Contreras", "SSY657", 12,  4300000, D(2026,8,12), D(2026,8,12)),
 ("G-2402", "P-5002", D(2026,8,11), "Distribuidora La Sabana",    "Chía",         "Transportadora A", "Juan Contreras", "SSY657",  8,  2100000, D(2026,8,13), D(2026,8,13)),
 ("G-2403", "P-5003", D(2026,8,13), "Almacén Los Andes",          "Bogotá",       "Transportadora A", "Marta Peña",     "KLM220",  5,  1500000, D(2026,8,15), D(2026,8,14)),
 ("G-2404", "P-5004", D(2026,8,17), "Insumos del Norte",          "Zipaquirá",    "Transportadora A", "Juan Contreras", "SSY657", 15,  5200000, D(2026,8,19), D(2026,8,19)),
 ("G-2405", "P-5005", D(2026,8,20), "Veterinaria San Jorge",      "Cota",         "Transportadora A", "Marta Peña",     "KLM220",  4,  1100000, D(2026,8,22), D(2026,8,22)),
 ("G-2406", "P-5006", D(2026,8,25), "Comercial El Prado",         "Bogotá",       "Transportadora A", "Juan Contreras", "SSY657",  9,  2800000, D(2026,8,27), D(2026,8,27)),
 ("G-2407", "P-5007", D(2026,8,28), "Agro Suministros SAS",       "Funza",        "Transportadora A", "Marta Peña",     "KLM220",  6,  1750000, D(2026,9,1),  D(2026,9,1)),
 ("G-2408", "P-5008", D(2026,9,2),  "Distribuidora La Sabana",    "Chía",         "Transportadora A", "Juan Contreras", "SSY657", 11,  3400000, D(2026,9,4),  D(2026,9,4)),
 # --- Transportadora B: intermedia ---
 ("G-2409", "P-5009", D(2026,8,10), "Almacén Central del Café",   "Pereira",      "Transportadora B", "Pedro Ruiz",     "ABC123",  7,  2050000, D(2026,8,14), D(2026,8,14)),
 ("G-2410", "P-5010", D(2026,8,12), "Mercados del Eje",           "Armenia",      "Transportadora B", "Pedro Ruiz",     "ABC123", 20,  7000000, D(2026,8,16), D(2026,8,18)),
 ("G-2411", "P-5011", D(2026,8,14), "Surtitodo Manizales",        "Manizales",    "Transportadora B", "Ivan Salas",     "RTF908", 10,  3100000, D(2026,8,18), D(2026,8,18)),
 ("G-2412", "P-5012", D(2026,8,19), "Agropecuaria del Quindío",   "Armenia",      "Transportadora B", "Pedro Ruiz",     "ABC123",  6,  1900000, D(2026,8,23), D(2026,8,23)),
 ("G-2413", "P-5013", D(2026,8,24), "Almacén Central del Café",   "Pereira",      "Transportadora B", "Ivan Salas",     "RTF908", 14,  4600000, D(2026,8,28), D(2026,8,31)),
 ("G-2414", "P-5014", D(2026,8,27), "Distribuciones Risaralda",   "Dosquebradas", "Transportadora B", "Pedro Ruiz",     "ABC123",  3,   850000, D(2026,8,31), D(2026,8,31)),
 ("G-2415", "P-5015", D(2026,9,1),  "Mercados del Eje",           "Armenia",      "Transportadora B", "Ivan Salas",     "RTF908", 18,  5900000, D(2026,9,5),  D(2026,9,7)),
 ("G-2416", "P-5016", D(2026,9,3),  "Surtitodo Manizales",        "Manizales",    "Transportadora B", "Pedro Ruiz",     "ABC123",  8,  2400000, D(2026,9,7),  D(2026,9,7)),
 # --- Transportadora C: la que hay que sentar a hablar ---
 ("G-2417", "P-5017", D(2026,8,11), "Comercial del Norte",        "Barranquilla", "Transportadora C", "Luis Gómez",     "XYZ987", 22,  7600000, D(2026,8,16), D(2026,8,20)),
 ("G-2418", "P-5018", D(2026,8,14), "Distribuidora Caribe",       "Santa Marta",  "Transportadora C", "Luis Gómez",     "XYZ987", 16,  5100000, D(2026,8,19), D(2026,8,19)),
 ("G-2419", "P-5019", D(2026,8,18), "Almacenes del Atlántico",    "Barranquilla", "Transportadora C", "Nelson Ríos",    "PLK441",  9,  2900000, D(2026,8,23), D(2026,8,27)),
 ("G-2420", "P-5020", D(2026,8,21), "Agro Costa SAS",             "Cartagena",    "Transportadora C", "Luis Gómez",     "XYZ987", 12,  3800000, D(2026,8,26), D(2026,8,29)),
 ("G-2421", "P-5021", D(2026,8,26), "Distribuidora Caribe",       "Santa Marta",  "Transportadora C", "Nelson Ríos",    "PLK441",  7,  2200000, D(2026,8,31), D(2026,8,31)),
 ("G-2422", "P-5022", D(2026,9,1),  "Comercial del Norte",        "Barranquilla", "Transportadora C", "Luis Gómez",     "XYZ987", 25,  8200000, D(2026,9,6),  D(2026,9,9)),
 ("G-2423", "P-5023", D(2026,9,4),  "Agro Costa SAS",             "Cartagena",    "Transportadora C", "Nelson Ríos",    "PLK441", 11,  3500000, D(2026,9,9),  None),
 # --- Flota propia ---
 ("G-2424", "P-5024", D(2026,8,12), "Agro Sur Ltda",              "Neiva",        "Flota propia",     "Ana Torres",     "QTZ531",  7,  1900000, D(2026,8,15), D(2026,8,15)),
 ("G-2425", "P-5025", D(2026,8,17), "Tienda El Campo",            "Villavicencio","Flota propia",     "Ana Torres",     "QTZ531",  3,   900000, D(2026,8,20), D(2026,8,22)),
 ("G-2426", "P-5026", D(2026,8,20), "Insumos del Llano",          "Villavicencio","Flota propia",     "Carlos Mena",    "HJU775", 13,  4100000, D(2026,8,23), D(2026,8,23)),
 ("G-2427", "P-5027", D(2026,8,24), "Agro Sur Ltda",              "Neiva",        "Flota propia",     "Ana Torres",     "QTZ531",  9,  2700000, D(2026,8,27), D(2026,8,27)),
 ("G-2428", "P-5028", D(2026,8,31), "Distribuidora del Huila",    "Pitalito",     "Flota propia",     "Carlos Mena",    "HJU775",  5,  1600000, D(2026,9,3),  D(2026,9,3)),
 ("G-2429", "P-5029", D(2026,9,2),  "Insumos del Llano",          "Villavicencio","Flota propia",     "Ana Torres",     "QTZ531", 10,  3200000, D(2026,9,5),  D(2026,9,5)),
 ("G-2430", "P-5030", D(2026,9,7),  "Tienda El Campo",            "Villavicencio","Flota propia",     "Carlos Mena",    "HJU775",  4,  1250000, D(2026,9,10), None),
]

# fecha, origen, guia, tipo, punto de ocurrencia, causa, unidades, valor,
# estado, responsable, fecha solucion, que se hizo, notas
NOVEDADES = [
 # ---------- EN RUTA ----------
 (D(2026,8,13), "En ruta", "G-2403", "Empaque en mal estado", "En ruta / entrega al cliente",
  "Embalaje o estibado deficiente", 1, 0, "Resuelta", "Jefe de bodega", D(2026,8,14),
  "Se cambió el empaque y se reforzó el estibado", ""),
 (D(2026,8,18), "En ruta", "G-2410", "Retraso en vía", "En ruta / entrega al cliente",
  "Tráfico, cierre vial u orden público", 0, 0, "Resuelta", "Analista de transporte", D(2026,8,19),
  "Cierre en La Línea; se reprogramó la ruta", ""),
 (D(2026,8,20), "En ruta", "G-2417", "Avería / producto dañado", "En ruta / entrega al cliente",
  "Manipulación brusca en cargue/descargue", 4, 1380000, "Resuelta", "Coordinador de logística",
  D(2026,8,25), "Nota crédito y recobro a la transportadora", "Se pidió reinducción al equipo de cargue"),
 (D(2026,8,20), "En ruta", "G-2417", "Faltante (llegó de menos)", "Alistamiento (picking)",
  "Error de alistamiento (picking)", 2, 690000, "Resuelta", "Jefe de bodega", D(2026,8,24),
  "Reconteo en bodega y despacho del faltante", ""),
 (D(2026,8,25), "En ruta", "G-2426", "Faltante (llegó de menos)", "Alistamiento (picking)",
  "Inventario descuadrado", 2, 630000, "Resuelta", "Jefe de bodega", D(2026,8,27),
  "Se despachó el faltante al día siguiente",
  "Llegó a tiempo pero incompleta: cuenta como entrega a tiempo y NO como OTIF"),
 (D(2026,8,27), "En ruta", "G-2419", "Cliente ausente / no atiende", "En ruta / entrega al cliente",
  "Datos del cliente desactualizados", 9, 2900000, "Resuelta", "Servicio al cliente", D(2026,8,31),
  "Se actualizó el contacto y se reprogramó", ""),
 (D(2026,8,31), "En ruta", "G-2420", "Cliente rechaza el envío", "En ruta / entrega al cliente",
  "Cliente sin cupo / cartera bloqueada", 12, 3800000, "Esperando al cliente", "Cartera", None, "",
  "Cartera está revisando el cupo"),
 (D(2026,8,31), "En ruta", "G-2413", "Producto equivocado", "Alistamiento (picking)",
  "Error de alistamiento (picking)", 3, 980000, "Resuelta", "Jefe de bodega", D(2026,9,3),
  "Se recogió y se despachó la referencia correcta", ""),
 (D(2026,9,2),  "En ruta", "G-2425", "Soporte de entrega sin firmar", "En ruta / entrega al cliente",
  "Conductor sin capacitación o procedimiento", 0, 0, "En gestión", "Analista de transporte", None, "",
  "Falta el sello del cliente"),
 (D(2026,9,7),  "En ruta", "G-2415", "Retraso en vía", "Despacho y coordinación",
  "Ruta mal planeada o secuencia errada", 0, 0, "En gestión", "Coordinador de logística", None, "",
  "Se está revisando la secuencia de entrega"),
 (D(2026,9,8),  "En ruta", "G-2422", "Avería / producto dañado", "Cargue del vehículo",
  "Manipulación brusca en cargue/descargue", 5, 1640000, "Escalada a transportadora",
  "Analista de transporte", None, "", "Tercer caso del mismo conductor"),
 (D(2026,9,8),  "En ruta", "G-2422", "Vehículo varado / falla mecánica", "En ruta / entrega al cliente",
  "Falla mecánica del vehículo", 25, 8200000, "Esperando a la transportadora",
  "Analista de transporte", None, "", "El vehículo quedó varado en la vía"),
 (D(2026,9,9),  "En ruta", "G-2423", "Retraso en vía", "En ruta / entrega al cliente",
  "Falla mecánica del vehículo", 11, 3500000, "Sin gestionar", "Coordinador de logística", None, "", ""),
 (D(2026,9,9),  "En ruta", "G-2416", "Error en factura o precio", "Facturación y documentos",
  "Error en facturación o precio", 0, 210000, "En gestión", "Facturación", None, "",
  "Diferencia de precio en dos referencias"),
 # ---------- INTERNAS (sin guía) ----------
 (D(2026,8,12), "Interna", None, "Error de alistamiento detectado en bodega", "Alistamiento (picking)",
  "Falta de espacio u orden en bodega", 6, 0, "Resuelta", "Jefe de bodega", D(2026,8,13),
  "Se reorganizó la zona de picking", "Detectado antes de despachar: no llegó al cliente"),
 (D(2026,8,19), "Interna", None, "Diferencia de inventario", "Almacenamiento",
  "Inventario descuadrado", 34, 1150000, "En gestión", "Jefe de bodega", None, "",
  "Conteo cíclico de la zona B"),
 (D(2026,8,21), "Interna", None, "Falla de equipo en bodega", "Cargue del vehículo",
  "Equipo de bodega fuera de servicio", 0, 480000, "Resuelta", "Jefe de operaciones", D(2026,8,24),
  "Se reparó el montacargas", "Dos días de cargue manual"),
 (D(2026,8,26), "Interna", None, "Demora en el cargue", "Cargue del vehículo",
  "Personal insuficiente en el turno", 0, 0, "Resuelta", "Jefe de operaciones", D(2026,8,27),
  "Se reforzó el turno de la mañana", ""),
 (D(2026,9,1),  "Interna", None, "Producto averiado en bodega", "Almacenamiento",
  "Falta de espacio u orden en bodega", 8, 2350000, "En gestión", "Jefe de bodega", None, "",
  "Estiba mal apilada en la zona de tránsito"),
 (D(2026,9,3),  "Interna", None, "Demora en facturación o documentos", "Facturación y documentos",
  "Documentación incompleta", 0, 0, "Resuelta", "Facturación", D(2026,9,4),
  "Se completaron los soportes", ""),
 (D(2026,9,7),  "Interna", None, "Devolución recibida sin soporte", "Bodega de devoluciones",
  "Procedimiento no seguido", 5, 720000, "Sin gestionar", "Jefe de bodega", None, "",
  "Llegó sin la remisión de retorno"),
 (D(2026,9,8),  "Interna", None, "Incidente de seguridad o accidente laboral", "Patio / zona de maniobras",
  "Procedimiento no seguido", 0, 0, "En gestión", "Seguridad y salud", None, "",
  "Golpe leve durante maniobra; se abrió investigación"),
]

wb = openpyxl.load_workbook(DEST)
ev, nv = wb["ENVIOS"], wb["NOVEDADES"]
for i, fila in enumerate(ENVIOS):
    for j, v in enumerate(fila):
        if v is not None:
            ev.cell(row=4 + i, column=1 + j, value=v)
COLS = ["B", "C", "D", "M", "P", "Q", "T", "U", "V", "W", "Y", "AB", "AC"]
for i, fila in enumerate(NOVEDADES):
    for col, v in zip(COLS, fila):
        if v not in (None, ""):
            nv[f"{col}{4 + i}"] = v
# el buscador arranca con un Nº de PEDIDO puesto, para que se vea que sirve
# tanto la guia como el pedido
wb["TABLERO"]["D113"] = "P-5017"
wb.save(DEST)
print("OK ->", DEST)
print(f"   {len(ENVIOS)} envíos, {len(NOVEDADES)} novedades")
