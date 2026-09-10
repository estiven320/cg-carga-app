# -*- coding: utf-8 -*-
"""Genera MATRIZ_NOVEDADES_..._EJEMPLO.xlsx: la misma matriz, ya con un mes
de datos ficticios cargados, para ver el tablero funcionando al abrirlo.

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
 ("G-2401", D(2026,8,10), "Agroveterinaria El Roble",   "Bogotá",       "Transportadora A", "Juan Contreras", "SSY657", 12,  4300000, D(2026,8,12), D(2026,8,12)),
 ("G-2402", D(2026,8,11), "Distribuidora La Sabana",    "Chía",         "Transportadora A", "Juan Contreras", "SSY657",  8,  2100000, D(2026,8,13), D(2026,8,13)),
 ("G-2403", D(2026,8,13), "Almacén Los Andes",          "Bogotá",       "Transportadora A", "Marta Peña",     "KLM220",  5,  1500000, D(2026,8,15), D(2026,8,14)),
 ("G-2404", D(2026,8,17), "Insumos del Norte",          "Zipaquirá",    "Transportadora A", "Juan Contreras", "SSY657", 15,  5200000, D(2026,8,19), D(2026,8,19)),
 ("G-2405", D(2026,8,20), "Veterinaria San Jorge",      "Cota",         "Transportadora A", "Marta Peña",     "KLM220",  4,  1100000, D(2026,8,22), D(2026,8,22)),
 ("G-2406", D(2026,8,25), "Comercial El Prado",         "Bogotá",       "Transportadora A", "Juan Contreras", "SSY657",  9,  2800000, D(2026,8,27), D(2026,8,27)),
 ("G-2407", D(2026,8,28), "Agro Suministros SAS",       "Funza",        "Transportadora A", "Marta Peña",     "KLM220",  6,  1750000, D(2026,9,1),  D(2026,9,1)),
 ("G-2408", D(2026,9,2),  "Distribuidora La Sabana",    "Chía",         "Transportadora A", "Juan Contreras", "SSY657", 11,  3400000, D(2026,9,4),  D(2026,9,4)),
 # --- Transportadora B: intermedia ---
 ("G-2409", D(2026,8,10), "Almacén Central del Café",   "Pereira",      "Transportadora B", "Pedro Ruiz",     "ABC123",  7,  2050000, D(2026,8,14), D(2026,8,14)),
 ("G-2410", D(2026,8,12), "Mercados del Eje",           "Armenia",      "Transportadora B", "Pedro Ruiz",     "ABC123", 20,  7000000, D(2026,8,16), D(2026,8,18)),
 ("G-2411", D(2026,8,14), "Surtitodo Manizales",        "Manizales",    "Transportadora B", "Ivan Salas",     "RTF908", 10,  3100000, D(2026,8,18), D(2026,8,18)),
 ("G-2412", D(2026,8,19), "Agropecuaria del Quindío",   "Armenia",      "Transportadora B", "Pedro Ruiz",     "ABC123",  6,  1900000, D(2026,8,23), D(2026,8,23)),
 ("G-2413", D(2026,8,24), "Almacén Central del Café",   "Pereira",      "Transportadora B", "Ivan Salas",     "RTF908", 14,  4600000, D(2026,8,28), D(2026,8,31)),
 ("G-2414", D(2026,8,27), "Distribuciones Risaralda",   "Dosquebradas", "Transportadora B", "Pedro Ruiz",     "ABC123",  3,   850000, D(2026,8,31), D(2026,8,31)),
 ("G-2415", D(2026,9,1),  "Mercados del Eje",           "Armenia",      "Transportadora B", "Ivan Salas",     "RTF908", 18,  5900000, D(2026,9,5),  D(2026,9,7)),
 ("G-2416", D(2026,9,3),  "Surtitodo Manizales",        "Manizales",    "Transportadora B", "Pedro Ruiz",     "ABC123",  8,  2400000, D(2026,9,7),  D(2026,9,7)),
 # --- Transportadora C: la que hay que sentar a hablar ---
 ("G-2417", D(2026,8,11), "Comercial del Norte",        "Barranquilla", "Transportadora C", "Luis Gómez",     "XYZ987", 22,  7600000, D(2026,8,16), D(2026,8,20)),
 ("G-2418", D(2026,8,14), "Distribuidora Caribe",       "Santa Marta",  "Transportadora C", "Luis Gómez",     "XYZ987", 16,  5100000, D(2026,8,19), D(2026,8,19)),
 ("G-2419", D(2026,8,18), "Almacenes del Atlántico",    "Barranquilla", "Transportadora C", "Nelson Ríos",    "PLK441",  9,  2900000, D(2026,8,23), D(2026,8,27)),
 ("G-2420", D(2026,8,21), "Agro Costa SAS",             "Cartagena",    "Transportadora C", "Luis Gómez",     "XYZ987", 12,  3800000, D(2026,8,26), D(2026,8,29)),
 ("G-2421", D(2026,8,26), "Distribuidora Caribe",       "Santa Marta",  "Transportadora C", "Nelson Ríos",    "PLK441",  7,  2200000, D(2026,8,31), D(2026,8,31)),
 ("G-2422", D(2026,9,1),  "Comercial del Norte",        "Barranquilla", "Transportadora C", "Luis Gómez",     "XYZ987", 25,  8200000, D(2026,9,6),  D(2026,9,9)),
 ("G-2423", D(2026,9,4),  "Agro Costa SAS",             "Cartagena",    "Transportadora C", "Nelson Ríos",    "PLK441", 11,  3500000, D(2026,9,9),  None),
 # --- Flota propia ---
 ("G-2424", D(2026,8,12), "Agro Sur Ltda",              "Neiva",        "Flota propia",     "Ana Torres",     "QTZ531",  7,  1900000, D(2026,8,15), D(2026,8,15)),
 ("G-2425", D(2026,8,17), "Tienda El Campo",            "Villavicencio","Flota propia",     "Ana Torres",     "QTZ531",  3,   900000, D(2026,8,20), D(2026,8,22)),
 ("G-2426", D(2026,8,20), "Insumos del Llano",          "Villavicencio","Flota propia",     "Carlos Mena",    "HJU775", 13,  4100000, D(2026,8,23), D(2026,8,23)),
 ("G-2427", D(2026,8,24), "Agro Sur Ltda",              "Neiva",        "Flota propia",     "Ana Torres",     "QTZ531",  9,  2700000, D(2026,8,27), D(2026,8,27)),
 ("G-2428", D(2026,8,31), "Distribuidora del Huila",    "Pitalito",     "Flota propia",     "Carlos Mena",    "HJU775",  5,  1600000, D(2026,9,3),  D(2026,9,3)),
 ("G-2429", D(2026,9,2),  "Insumos del Llano",          "Villavicencio","Flota propia",     "Ana Torres",     "QTZ531", 10,  3200000, D(2026,9,5),  D(2026,9,5)),
 ("G-2430", D(2026,9,7),  "Tienda El Campo",            "Villavicencio","Flota propia",     "Carlos Mena",    "HJU775",  4,  1250000, D(2026,9,10), None),
]

# fecha, guia, tipo, causa, und, valor, estado, responsable, fsolucion, que se hizo, notas
NOVEDADES = [
 (D(2026,8,13), "G-2403", "Empaque en mal estado", "Embalaje o estibado deficiente",
  1, 0, "Resuelta", "Jefe de bodega", D(2026,8,14), "Se cambió el empaque y se reforzó el estibado", ""),
 (D(2026,8,18), "G-2410", "Retraso en vía", "Tráfico, cierre vial u orden público",
  0, 0, "Resuelta", "Analista de transporte", D(2026,8,19), "Cierre en La Línea; se reprogramó la ruta", ""),
 (D(2026,8,20), "G-2417", "Avería / producto dañado", "Manipulación brusca en cargue/descargue",
  4, 1380000, "Resuelta", "Coordinador de logística", D(2026,8,25), "Nota crédito y recobro a la transportadora", "Se pidió reinducción al equipo de cargue"),
 (D(2026,8,20), "G-2417", "Faltante (llegó de menos)", "Error de alistamiento (picking)",
  2, 690000, "Resuelta", "Jefe de bodega", D(2026,8,24), "Reconteo en bodega y despacho del faltante", ""),
 (D(2026,8,27), "G-2419", "Cliente ausente / no atiende", "Datos del cliente desactualizados",
  9, 2900000, "Resuelta", "Servicio al cliente", D(2026,8,31), "Se actualizó el contacto y se reprogramó", ""),
 (D(2026,8,31), "G-2420", "Cliente rechaza el envío", "Cliente sin cupo / cartera bloqueada",
  12, 3800000, "Esperando al cliente", "Cartera", None, "", "Cartera está revisando el cupo"),
 (D(2026,8,31), "G-2413", "Producto equivocado", "Error de alistamiento (picking)",
  3, 980000, "Resuelta", "Jefe de bodega", D(2026,9,3), "Se recogió y se despachó la referencia correcta", ""),
 (D(2026,8,25), "G-2426", "Faltante (llegó de menos)", "Inventario descuadrado",
  2, 630000, "Resuelta", "Jefe de bodega", D(2026,8,27), "Se despachó el faltante al día siguiente",
  "Llegó a tiempo pero incompleta: cuenta como entrega a tiempo y NO como OTIF"),
 (D(2026,9,2),  "G-2425", "Soporte de entrega sin firmar", "Conductor sin capacitación o procedimiento",
  0, 0, "En gestión", "Analista de transporte", None, "", "Falta el sello del cliente"),
 (D(2026,9,7),  "G-2415", "Retraso en vía", "Ruta mal planeada o secuencia errada",
  0, 0, "En gestión", "Coordinador de logística", None, "", "Se está revisando la secuencia de entrega"),
 (D(2026,9,8),  "G-2422", "Avería / producto dañado", "Manipulación brusca en cargue/descargue",
  5, 1640000, "Escalada a transportadora", "Analista de transporte", None, "", "Tercer caso del mismo conductor"),
 (D(2026,9,8),  "G-2422", "Vehículo varado / falla mecánica", "Falla mecánica del vehículo",
  25, 8200000, "Esperando a la transportadora", "Analista de transporte", None, "", "El vehículo quedó varado en la vía"),
 (D(2026,9,9),  "G-2423", "Retraso en vía", "Falla mecánica del vehículo",
  11, 3500000, "Sin gestionar", "Coordinador de logística", None, "", ""),
 (D(2026,9,9),  "G-2416", "Error en factura o precio", "Error en facturación",
  0, 210000, "En gestión", "Facturación", None, "", "Diferencia de precio en dos referencias"),
]

wb = openpyxl.load_workbook(DEST)
ev, nv = wb["ENVIOS"], wb["NOVEDADES"]
for i, fila in enumerate(ENVIOS):
    for j, v in enumerate(fila):
        if v is not None:
            ev.cell(row=4 + i, column=1 + j, value=v)
COLS = ["B", "C", "K", "N", "Q", "R", "S", "T", "V", "Y", "Z"]
for i, fila in enumerate(NOVEDADES):
    for col, v in zip(COLS, fila):
        if v not in (None, ""):
            nv[f"{col}{4 + i}"] = v
wb.save(DEST)
print("OK ->", DEST)
print(f"   {len(ENVIOS)} envíos, {len(NOVEDADES)} novedades")
