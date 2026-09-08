# -*- coding: utf-8 -*-
"""Valida las consultas M sin abrir Power BI.

Simula paso a paso el conjunto de columnas de cada consulta (partiendo de los
encabezados reales del libro) y comprueba que toda columna referenciada exista
en ese punto del flujo. Detecta erratas de tildes, renombrados a un nombre ya
existente y columnas seleccionadas que nunca se crearon.
"""
import re
import sys

import openpyxl

STR = re.compile(r'"((?:[^"\\]|\\.)*)"')


def encabezados(ruta_xlsx):
    wb = openpyxl.load_workbook(ruta_xlsx, read_only=True)
    return {
        ws.title: [str(c.value) for c in next(ws.iter_rows(max_row=1))]
        for ws in wb.worksheets
    }


def dividir_pasos(m):
    """Devuelve [(nombre, expresion)] de los pasos del bloque let de nivel 1."""
    cuerpo = m[m.index("let") + 3 : m.rindex("in")]
    # Los comentarios pueden contener comas y parentesis: se quitan antes de dividir.
    cuerpo = "\n".join(l for l in cuerpo.splitlines() if not l.strip().startswith("//"))
    pasos, prof, ini = [], 0, 0
    for i, ch in enumerate(cuerpo):
        if ch in "({[":
            prof += 1
        elif ch in ")}]":
            prof -= 1
        elif ch == "," and prof == 0:
            pasos.append(cuerpo[ini:i])
            ini = i + 1
    pasos.append(cuerpo[ini:])
    salida = []
    for p in pasos:
        p = p.strip()
        if not p or p.startswith("//"):
            continue
        p = "\n".join(l for l in p.splitlines() if not l.strip().startswith("//")).strip()
        if "=" not in p:
            continue
        nombre, expr = p.split("=", 1)
        salida.append((nombre.strip(), expr.strip()))
    return salida


def listas_llaves(expr):
    """Listas {...} de primer nivel dentro de la llamada."""
    dentro = expr[expr.index("(") + 1 : expr.rindex(")")]
    out, prof, ini = [], 0, None
    for i, ch in enumerate(dentro):
        if ch == "{":
            if prof == 0:
                ini = i + 1
            prof += 1
        elif ch == "}":
            prof -= 1
            if prof == 0:
                out.append(dentro[ini:i])
    return out


def simular(nombre, m, hdr, cols_externas, errores):
    pasos = dividir_pasos(m)
    entorno = {}

    def cols_de(expr):
        """Columnas de la tabla de entrada: primer identificador ya conocido.

        Recorre los identificadores en orden textual porque la tabla de entrada
        puede venir de una llamada anidada, p.ej. Table.Distinct(Table.SelectColumns(T, ...)).
        """
        for ident in re.findall(r"[A-Za-z_][A-Za-z0-9_]*", expr):
            if ident in entorno:
                return list(entorno[ident])
            if ident in cols_externas:
                return list(cols_externas[ident])
        return None

    def err(msg):
        errores.append(f"{nombre}: {msg}")

    for paso, expr in pasos:
        fn = re.match(r"([A-Za-z_][A-Za-z0-9_.]*)\s*\(", expr)
        fname = fn.group(1) if fn else ""
        cols = cols_de(expr)

        if fname == "fnHoja":
            hoja = STR.search(expr).group(1)
            if hoja not in hdr:
                err(f"la hoja '{hoja}' no existe en el libro")
                cols = []
            else:
                cols = list(hdr[hoja])

        elif fname == "Table.SelectColumns":
            pedidas = STR.findall(listas_llaves(expr)[0])
            for c in pedidas:
                if cols is not None and c not in cols:
                    err(f"paso {paso}: SelectColumns pide '{c}', no existe (hay: {len(cols)} cols)")
            cols = pedidas

        elif fname == "Table.RenameColumns":
            pares = re.findall(r'\{\s*"((?:[^"\\]|\\.)*)"\s*,\s*"((?:[^"\\]|\\.)*)"\s*\}', listas_llaves(expr)[0])
            cols = list(cols or [])
            for viejo, nuevo in pares:
                if viejo not in cols:
                    err(f"paso {paso}: RenameColumns pide '{viejo}', no existe")
                elif viejo == nuevo:
                    err(f"paso {paso}: RenameColumns renombra '{viejo}' a si mismo (M falla)")
                elif nuevo in cols and nuevo != viejo:
                    err(f"paso {paso}: RenameColumns crea '{nuevo}' que ya existe")
                else:
                    cols[cols.index(viejo)] = nuevo

        elif fname in ("Table.TransformColumnTypes", "Table.TransformColumns"):
            for bloque in re.findall(r'\{\s*"((?:[^"\\]|\\.)*)"\s*,', listas_llaves(expr)[0]):
                if cols is not None and bloque not in cols:
                    err(f"paso {paso}: {fname} toca '{bloque}', no existe")

        elif fname == "Table.AddColumn":
            nueva = STR.search(expr).group(1)
            cols = list(cols or [])
            if nueva in cols:
                err(f"paso {paso}: AddColumn crea '{nueva}' que ya existe")
            else:
                cols.append(nueva)

        elif fname == "Table.RemoveColumns":
            quitar = STR.findall(listas_llaves(expr)[0])
            cols = list(cols or [])
            for c in quitar:
                if c not in cols:
                    err(f"paso {paso}: RemoveColumns quita '{c}', no existe")
                else:
                    cols.remove(c)

        elif fname == "Table.NestedJoin":
            ls = listas_llaves(expr)
            cols = list(cols or [])
            for c in STR.findall(ls[0]):
                if c not in cols:
                    err(f"paso {paso}: NestedJoin usa clave izquierda '{c}', no existe")
            otra = re.findall(r"\}\s*,\s*([A-Za-z_][A-Za-z0-9_]*)\s*,", expr)
            destino = cols_externas.get(otra[0]) if otra else None
            if destino is not None:
                for c in STR.findall(ls[1]):
                    if c not in destino:
                        err(f"paso {paso}: NestedJoin usa clave derecha '{c}', no existe en {otra[0]}")
            cols.append(STR.findall(expr)[-1])

        elif fname == "Table.ExpandTableColumn":
            ls = listas_llaves(expr)
            anidada = STR.search(expr).group(1)
            cols = list(cols or [])
            if anidada in cols:
                cols.remove(anidada)
            nuevos = STR.findall(ls[1]) if len(ls) > 1 else STR.findall(ls[0])
            for c in nuevos:
                if c in cols:
                    err(f"paso {paso}: Expand crea '{c}' que ya existe")
                else:
                    cols.append(c)

        elif fname in ("Table.Distinct", "Table.Sort"):
            interno = re.search(r"Table\.SelectColumns\([^,]+,\s*\{([^}]*)\}", expr)
            if interno:
                pedidas = STR.findall(interno.group(1))
                for c in pedidas:
                    if cols is not None and c not in cols:
                        err(f"paso {paso}: SelectColumns anidado pide '{c}', no existe")
                cols = pedidas
            else:
                ls = listas_llaves(expr)
                if ls:
                    for c in STR.findall(ls[0]):
                        if cols is not None and c not in cols:
                            err(f"paso {paso}: {fname} usa '{c}', no existe")

        elif fname == "Table.FromRows":
            cols = STR.findall(listas_llaves(expr)[-1])

        # SelectRows y demas no alteran el conjunto de columnas.
        entorno[paso] = cols if cols is not None else []

    return entorno[pasos[-1][0]]


def main(ruta_xlsx):
    sys.path.insert(0, __file__.rsplit("/", 1)[0])
    import modelo

    hdr = encabezados(ruta_xlsx)
    errores = []
    externas = {}
    orden = [
        ("Dim_Clientes", modelo.M_DIM_CLIENTES),
        ("Fact_Guias", modelo.M_FACT_GUIAS),
        ("Dim_Productos", modelo.M_DIM_PRODUCTOS),
        ("Dim_Calendario", modelo.M_DIM_CALENDARIO),
        ("Dim_Transportadora", modelo.M_DIM_TRANSPORTADORA),
        ("Dim_Ruta", modelo.M_DIM_RUTA),
        ("Fact_Devoluciones", modelo.M_FACT_DEVOLUCIONES),
        ("_Medidas", modelo.M_MEDIDAS),
    ]
    for nombre, m in orden:
        externas[nombre] = simular(nombre, m, hdr, externas, errores)

    for e in errores:
        print("ERROR:", e)
    if not errores:
        print("OK: consultas M coherentes con el libro")
        for n, c in externas.items():
            print(f"  {n}: {len(c)} columnas -> {', '.join(c)}")
    return 1 if errores else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
