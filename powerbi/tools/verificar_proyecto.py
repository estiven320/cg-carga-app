# -*- coding: utf-8 -*-
"""Verifica el proyecto PBIP ya generado, leyendo los archivos del disco.

No sustituye a abrirlo en Power BI Desktop, pero descarta los fallos que
impiden que un PBIP cargue: JSON mal formado, referencias del informe a
campos que no existen en el modelo, relaciones colgantes, paginas sin
carpeta y visuales fuera del lienzo o superpuestos.

Uso:  python3 powerbi/tools/verificar_proyecto.py powerbi/GESTOAGRO
"""
import json
import os
import re
import sys

ANCHO, ALTO = 1280, 720


def leer_tmdl(carpeta):
    """Extrae tablas -> {columnas, medidas, sortBy} de los .tmdl."""
    modelo = {}
    tdir = os.path.join(carpeta, "definition", "tables")
    for archivo in sorted(os.listdir(tdir)):
        texto = open(os.path.join(tdir, archivo), encoding="utf-8").read()
        m = re.search(r"^table\s+(.+)$", texto, re.M)
        tabla = desquote(m.group(1).strip())
        cols, meds, sorts = set(), set(), {}
        for linea in texto.splitlines():
            s = linea.strip()
            c = re.match(r"^column\s+(.+?)(?:\s*=.*)?$", s)
            if c and linea.startswith("\tcolumn"):
                cols.add(desquote(c.group(1).strip()))
            d = re.match(r"^measure\s+(.+?)\s*=", s)
            if d and linea.startswith("\tmeasure"):
                meds.add(desquote(d.group(1).strip()))
            sb = re.match(r"^sortByColumn:\s*(.+)$", s)
            if sb:
                sorts[sorted(cols)[-1] if cols else "?"] = desquote(sb.group(1).strip())
        tiene_particion = "\tpartition " in texto
        modelo[tabla] = {"columnas": cols, "medidas": meds, "particion": tiene_particion}
    return modelo


def desquote(n):
    n = n.strip()
    if n.startswith("'") and n.endswith("'"):
        return n[1:-1].replace("''", "'")
    return n


def main(base):
    errores, avisos = [], []
    sm = [d for d in os.listdir(base) if d.endswith(".SemanticModel")][0]
    rp = [d for d in os.listdir(base) if d.endswith(".Report")][0]
    smd, rpd = os.path.join(base, sm), os.path.join(base, rp)

    # 1. Todos los JSON parsean
    n_json = 0
    for raiz, _, archivos in os.walk(base):
        for a in archivos:
            if a.endswith(".json") or a.endswith(".pbip") or a.endswith(".pbir") or a.endswith(".pbism") or a == ".platform":
                ruta = os.path.join(raiz, a)
                try:
                    json.load(open(ruta, encoding="utf-8"))
                    n_json += 1
                except Exception as e:
                    errores.append(f"JSON invalido {os.path.relpath(ruta, base)}: {e}")

    modelo = leer_tmdl(smd)

    # 2. model.tmdl: cada 'ref table' tiene archivo, y cada tabla tiene particion
    mdl = open(os.path.join(smd, "definition", "model.tmdl"), encoding="utf-8").read()
    for t in re.findall(r"^ref table\s+(.+)$", mdl, re.M):
        t = desquote(t.strip())
        if t not in modelo:
            errores.append(f"model.tmdl declara 'ref table {t}' pero no existe tables/{t}.tmdl")
    for t, info in modelo.items():
        if not info["particion"]:
            errores.append(f"la tabla {t} no tiene particion")
        if t not in [desquote(x.strip()) for x in re.findall(r"^ref table\s+(.+)$", mdl, re.M)]:
            errores.append(f"la tabla {t} existe como archivo pero no esta en model.tmdl")

    # 3. Relaciones: los extremos existen
    rel = open(os.path.join(smd, "definition", "relationships.tmdl"), encoding="utf-8").read()
    for lado, tabla, col in re.findall(r"^\t(fromColumn|toColumn):\s*([^.]+)\.(.+)$", rel, re.M):
        tabla, col = desquote(tabla), desquote(col)
        if tabla not in modelo:
            errores.append(f"relacion {lado}: la tabla {tabla} no existe")
        elif col not in modelo[tabla]["columnas"]:
            errores.append(f"relacion {lado}: {tabla}[{col}] no existe")

    # 4. Paginas declaradas == carpetas en disco
    pdir = os.path.join(rpd, "definition", "pages")
    meta = json.load(open(os.path.join(pdir, "pages.json"), encoding="utf-8"))
    carpetas = {d for d in os.listdir(pdir) if os.path.isdir(os.path.join(pdir, d))}
    if set(meta["pageOrder"]) != carpetas:
        errores.append(f"pageOrder {meta['pageOrder']} no coincide con las carpetas {sorted(carpetas)}")
    if meta.get("activePageName") not in carpetas:
        errores.append("activePageName apunta a una pagina inexistente")

    # 5. Visuales: referencias, lienzo y solapamientos
    n_vis = 0
    for pid in meta["pageOrder"]:
        pg = json.load(open(os.path.join(pdir, pid, "page.json"), encoding="utf-8"))
        if pg["name"] != pid:
            errores.append(f"page.json de {pid} declara name={pg['name']}")
        cajas = []
        vdir = os.path.join(pdir, pid, "visuals")
        for vid in sorted(os.listdir(vdir)):
            n_vis += 1
            v = json.load(open(os.path.join(vdir, vid, "visual.json"), encoding="utf-8"))
            if v["name"] != vid:
                errores.append(f"{pid}/{vid}: el campo name dice {v['name']}")
            p = v["position"]
            if p["x"] < 0 or p["y"] < 0 or p["x"] + p["width"] > ANCHO or p["y"] + p["height"] > ALTO:
                errores.append(f"{pid}/{vid}: se sale del lienzo ({p['x']},{p['y']} {p['width']}x{p['height']})")
            cajas.append((vid, p))

            for rol, estado in v["visual"].get("query", {}).get("queryState", {}).items():
                for pr in estado["projections"]:
                    tabla, prop = pr["queryRef"].split(".", 1)
                    f = pr["field"]
                    if tabla not in modelo:
                        errores.append(f"{pid}/{vid}[{rol}]: tabla {tabla} no existe")
                        continue
                    if "Measure" in f:
                        if prop not in modelo[tabla]["medidas"]:
                            errores.append(f"{pid}/{vid}[{rol}]: medida {tabla}[{prop}] no existe")
                    elif prop not in modelo[tabla]["columnas"]:
                        errores.append(f"{pid}/{vid}[{rol}]: columna {tabla}[{prop}] no existe")
                    if f.get("Measure", f.get("Column"))["Expression"]["SourceRef"]["Entity"] != tabla:
                        errores.append(f"{pid}/{vid}[{rol}]: Entity no coincide con queryRef")

        for i in range(len(cajas)):
            for j in range(i + 1, len(cajas)):
                a, b = cajas[i][1], cajas[j][1]
                sx = max(0, min(a["x"] + a["width"], b["x"] + b["width"]) - max(a["x"], b["x"]))
                sy = max(0, min(a["y"] + a["height"], b["y"] + b["height"]) - max(a["y"], b["y"]))
                if sx * sy > 0:
                    avisos.append(f"{pid}: {cajas[i][0]} y {cajas[j][0]} se solapan {sx}x{sy} px")

    for e in errores:
        print("ERROR:", e)
    for a in avisos:
        print("AVISO:", a)
    print()
    print(f"{n_json} archivos JSON validos | {len(modelo)} tablas | "
          f"{sum(len(v['medidas']) for v in modelo.values())} medidas | "
          f"{sum(len(v['columnas']) for v in modelo.values())} columnas | "
          f"{len(meta['pageOrder'])} paginas | {n_vis} visuales")
    print("RESULTADO:", "sin errores" if not errores else f"{len(errores)} error(es)")
    return 1 if errores else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
