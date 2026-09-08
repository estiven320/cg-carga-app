# -*- coding: utf-8 -*-
"""Consultas M del modelo semantico GESTOAGRO.

Los nombres de columna de origen son EXACTAMENTE los del libro de Excel
(con tildes); los nombres de destino son los que ve el usuario en el informe.
"""
import uuid

NS = uuid.UUID("6f1a5b2c-9d3e-4a71-8c25-1f0e7b4d9a63")


def lt(*parts):
    """LineageTag deterministico, para que regenerar no cambie el proyecto."""
    return str(uuid.uuid5(NS, "|".join(parts)))


RUTA_DEFECTO = r"C:\Users\braya\OneDrive\Escritorio\power bi\GESTOAGRO_PowerBI_datos.xlsx"

FN_HOJA = '''let
    Fn = (NombreHoja as text) as table =>
        let
            Libro = Excel.Workbook(File.Contents(RutaArchivo), null, true),
            Hoja = Libro{[Item = NombreHoja, Kind = "Sheet"]}[Data],
            Encabezados = Table.PromoteHeaders(Hoja, [PromoteAllScalars = true])
        in
            Encabezados
in
    Fn'''

M_FACT_GUIAS = '''let
    // ---- Despachos: aporta peso y datos de transporte ----
    Desp0 = fnHoja("Fact_Despachos"),
    Desp1 = Table.SelectColumns(Desp0, {"# Planilla", "# Pedido", "# Factura", "NOMBRE CLIENTE", "PESO KG", "EMPRESA TRANSPORTE", "TRANSPORTADOR", "PLACA", "RUTA", "FECHA DESPACHO"}),
    Desp2 = Table.RenameColumns(Desp1, {{"# Planilla", "Planilla"}, {"# Pedido", "Pedido"}, {"# Factura", "Factura"}, {"NOMBRE CLIENTE", "Cliente"}, {"PESO KG", "Peso KG"}, {"EMPRESA TRANSPORTE", "Transportadora"}, {"TRANSPORTADOR", "Transportador"}, {"PLACA", "Placa"}, {"RUTA", "Ruta Despacho"}, {"FECHA DESPACHO", "Fecha Despacho"}}),
    Desp3 = Table.SelectRows(Desp2, each [Planilla] <> null),
    Desp4 = Table.TransformColumnTypes(Desp3, {{"Planilla", Int64.Type}, {"Pedido", Int64.Type}, {"Factura", Int64.Type}, {"Cliente", type text}, {"Peso KG", type number}, {"Transportadora", type text}, {"Transportador", type text}, {"Placa", type text}, {"Ruta Despacho", type text}, {"Fecha Despacho", type date}}),

    // ---- Cumplidos: aporta plazo, fecha limite y estado de entrega ----
    Cum0 = fnHoja("Fact_Cumplidos"),
    Cum1 = Table.SelectColumns(Cum0, {"# Planilla", "# Pedido", "# Factura", "Ciudad", "Ruta", "Plazo (días)", "Fecha límite", "Estado cumplido", "Fecha recibido", "Días transcurridos", "Días de mora", "Semáforo", "Responsable", "Observaciones"}),
    Cum2 = Table.RenameColumns(Cum1, {{"# Planilla", "Planilla"}, {"# Pedido", "Pedido"}, {"# Factura", "Factura"}, {"Ciudad", "Ciudad Guia"}, {"Ruta", "Ruta Cumplido"}, {"Plazo (días)", "Plazo Días"}, {"Fecha límite", "Fecha Límite"}, {"Estado cumplido", "Estado Cumplido"}, {"Fecha recibido", "Fecha Recibido"}, {"Días transcurridos", "Días Transcurridos"}, {"Días de mora", "Días Mora Origen"}, {"Semáforo", "Semáforo Origen"}}),
    Cum3 = Table.SelectRows(Cum2, each [Planilla] <> null),
    Cum4 = Table.TransformColumnTypes(Cum3, {{"Planilla", Int64.Type}, {"Pedido", Int64.Type}, {"Factura", Int64.Type}, {"Ciudad Guia", type text}, {"Ruta Cumplido", type text}, {"Plazo Días", Int64.Type}, {"Fecha Límite", type date}, {"Estado Cumplido", type text}, {"Fecha Recibido", type date}, {"Días Transcurridos", Int64.Type}, {"Días Mora Origen", Int64.Type}, {"Semáforo Origen", type text}, {"Responsable", type text}, {"Observaciones", type text}}),

    // ---- Union por clave compuesta Planilla + Pedido + Factura (unica, 183/183) ----
    Union0 = Table.NestedJoin(Desp4, {"Planilla", "Pedido", "Factura"}, Cum4, {"Planilla", "Pedido", "Factura"}, "cum", JoinKind.LeftOuter),
    Union1 = Table.ExpandTableColumn(Union0, "cum", {"Ciudad Guia", "Ruta Cumplido", "Plazo Días", "Fecha Límite", "Estado Cumplido", "Fecha Recibido", "Días Transcurridos", "Días Mora Origen", "Semáforo Origen", "Responsable", "Observaciones"}),

    // ---- Clave de cliente normalizada y enriquecimiento desde el maestro ----
    Key0 = Table.AddColumn(Union1, "ClienteKey", each Text.Upper(Text.Trim([Cliente])), type text),
    Key1 = Table.NestedJoin(Key0, {"ClienteKey"}, Dim_Clientes, {"ClienteKey"}, "cli", JoinKind.LeftOuter),
    Key2 = Table.ExpandTableColumn(Key1, "cli", {"ClienteKey", "Ciudad", "Vendedor"}, {"ClienteKeyMaestro", "Ciudad Maestro", "Vendedor"}),

    // ---- Ciudad: la de la guia; si falta, la del maestro de clientes ----
    Ciu0 = Table.AddColumn(Key2, "Ciudad", each
        if [Ciudad Guia] <> null and Text.Trim([Ciudad Guia]) <> "" then Text.Upper(Text.Trim([Ciudad Guia]))
        else if [Ciudad Maestro] <> null and Text.Trim([Ciudad Maestro]) <> "" then Text.Upper(Text.Trim([Ciudad Maestro]))
        else "SIN CIUDAD", type text),
    Ciu1 = Table.AddColumn(Ciu0, "Origen Ciudad", each
        if [Ciudad Guia] <> null and Text.Trim([Ciudad Guia]) <> "" then "Guía"
        else if [Ciudad Maestro] <> null and Text.Trim([Ciudad Maestro]) <> "" then "Maestro de clientes"
        else "Sin dato", type text),

    // ---- Ruta: la de cumplidos; si falta, la de despachos ----
    Rut0 = Table.AddColumn(Ciu1, "Ruta", each
        if [Ruta Cumplido] <> null and Text.Trim([Ruta Cumplido]) <> "" then Text.Upper(Text.Trim([Ruta Cumplido]))
        else if [Ruta Despacho] <> null and Text.Trim([Ruta Despacho]) <> "" then Text.Upper(Text.Trim([Ruta Despacho]))
        else "SIN RUTA", type text),

    Cal0 = Table.AddColumn(Rut0, "Cliente en Maestro", each [ClienteKeyMaestro] <> null, type logical),
    Cal1 = Table.AddColumn(Cal0, "GuiaID", each Text.From([Planilla]) & "-" & Text.From([Pedido]) & "-" & Text.From([Factura]), type text),

    Final = Table.SelectColumns(Cal1, {"GuiaID", "Planilla", "Pedido", "Factura", "Cliente", "ClienteKey", "Cliente en Maestro", "Vendedor", "Ciudad", "Origen Ciudad", "Ruta", "Transportadora", "Transportador", "Placa", "Peso KG", "Fecha Despacho", "Plazo Días", "Fecha Límite", "Días Transcurridos", "Días Mora Origen", "Semáforo Origen", "Estado Cumplido", "Fecha Recibido", "Responsable", "Observaciones"})
in
    Final'''

M_DIM_CLIENTES = '''let
    Origen = fnHoja("Dim_Clientes"),
    NoNulos = Table.SelectRows(Origen, each [#"Nombre SN"] <> null and Text.Trim(Text.From([#"Nombre SN"])) <> ""),
    Renombrado = Table.RenameColumns(NoNulos, {{"Nombre de dirección", "Dirección"}, {"BARRIO", "Barrio"}, {"Teléfono móvil", "Teléfono"}, {"Correo electrónico", "Correo"}, {"Nombre de la lista de precios", "Lista de Precios"}, {"Nombre de empleado del departamento de ventas", "Vendedor"}}),
    Tipos = Table.TransformColumnTypes(Renombrado, {{"Código SN", type text}, {"Nombre SN", type text}, {"Dirección", type text}, {"Calle", type text}, {"Barrio", type text}, {"Ciudad", type text}, {"Teléfono", type text}, {"Correo", type text}, {"Lista de Precios", type text}, {"Vendedor", type text}}),
    CiudadUp = Table.TransformColumns(Tipos, {{"Ciudad", each if _ = null then null else Text.Upper(Text.Trim(_)), type text}}),
    ConKey = Table.AddColumn(CiudadUp, "ClienteKey", each Text.Upper(Text.Trim([#"Nombre SN"])), type text),
    // "Nombre SN" trae 9 nombres duplicados (codigos con error de digitacion).
    // Se conserva un solo registro por nombre para que la relacion sea 1 a varios.
    Ordenado = Table.Sort(ConKey, {{"Código SN", Order.Ascending}}),
    Unicos = Table.Distinct(Ordenado, {"ClienteKey"}),
    Final = Table.SelectColumns(Unicos, {"ClienteKey", "Código SN", "Nombre SN", "Ciudad", "Dirección", "Calle", "Barrio", "Teléfono", "Correo", "Lista de Precios", "Vendedor"})
in
    Final'''

M_DIM_PRODUCTOS = '''let
    Origen = fnHoja("Dim_Productos"),
    NoNulos = Table.SelectRows(Origen, each [#"COD PRODUCTO"] <> null),
    Renombrado = Table.RenameColumns(NoNulos, {{"COD PRODUCTO", "Código Producto"}, {"LINEA", "Línea"}, {"COD LINEA", "Código Línea"}, {"DESCRIPCION LINEA", "Descripción Línea"}, {"DESCRIPCION PRODUCTO", "Descripción Producto"}, {"PESO KG", "Peso KG"}, {"UND_EMPAQUE", "Unidad Empaque"}, {"GRUPO", "Grupo"}, {"COD GRUPO", "Código Grupo"}, {"DESCRIPCION GRUPO", "Descripción Grupo"}, {"REFERENCIA", "Referencia"}}),
    Tipos = Table.TransformColumnTypes(Renombrado, {{"Código Producto", type text}, {"Línea", type text}, {"Código Línea", type text}, {"Descripción Línea", type text}, {"Descripción Producto", type text}, {"Peso KG", type number}, {"Unidad Empaque", type text}, {"Estado Peso", type text}, {"Grupo", type text}, {"Código Grupo", type text}, {"Descripción Grupo", type text}, {"Referencia", type text}}),
    Unicos = Table.Distinct(Tipos, {"Código Producto"}),
    Final = Table.SelectColumns(Unicos, {"Código Producto", "Descripción Producto", "Línea", "Descripción Línea", "Grupo", "Descripción Grupo", "Peso KG", "Unidad Empaque", "Estado Peso", "Referencia"})
in
    Final'''

M_DIM_CALENDARIO = '''let
    Origen = fnHoja("Dim_Calendario"),
    NoNulos = Table.SelectRows(Origen, each [Fecha] <> null),
    Tipos = Table.TransformColumnTypes(NoNulos, {{"Fecha", type date}, {"Año", Int64.Type}, {"Trimestre", Int64.Type}, {"MesNum", Int64.Type}, {"Mes", type text}, {"Semana", Int64.Type}, {"DiaSemNum", Int64.Type}, {"DiaSemana", type text}}),
    AnioMes = Table.AddColumn(Tipos, "Año-Mes", each Text.From([Año]) & "-" & Text.PadStart(Text.From([MesNum]), 2, "0"), type text),
    AnioMesOrden = Table.AddColumn(AnioMes, "Año-Mes Orden", each [Año] * 100 + [MesNum], Int64.Type),
    Finde = Table.AddColumn(AnioMesOrden, "Es Fin de Semana", each [DiaSemNum] >= 6, type logical),
    Trim = Table.AddColumn(Finde, "Trimestre Nombre", each "T" & Text.From([Trimestre]), type text)
in
    Trim'''

M_DIM_TRANSPORTADORA = '''let
    Base = Table.Distinct(Table.SelectColumns(Fact_Guias, {"Transportadora"})),
    NoNulos = Table.SelectRows(Base, each [Transportadora] <> null),
    // Supuesto editable: CG CARGA y GESTO AGRO se tratan como flota propia.
    Tipo = Table.AddColumn(NoNulos, "Tipo Transportadora", each
        if List.Contains({"CG CARGA SAS", "GESTO AGRO S.A.S"}, [Transportadora]) then "Flota propia"
        else if [Transportadora] = "PERSONA NATURAL" then "Persona natural"
        else "Tercero", type text),
    Ordenado = Table.Sort(Tipo, {{"Transportadora", Order.Ascending}})
in
    Ordenado'''

M_DIM_RUTA = '''let
    Base = Table.Distinct(Table.SelectColumns(Fact_Guias, {"Ruta"})),
    NoNulos = Table.SelectRows(Base, each [Ruta] <> null),
    Zona = Table.AddColumn(NoNulos, "Zona", each
        if Text.StartsWith([Ruta], "BOGOTA") or List.Contains({"SUBA", "CORABASTOS", "CENCOSUD", "CHIA", "COTA", "SOACHA", "MOSQUERA", "FUNZA"}, [Ruta]) then "Bogotá y sabana"
        else if [Ruta] = "SIN RUTA" then "Sin clasificar"
        else "Nacional", type text),
    Ordenado = Table.Sort(Zona, {{"Ruta", Order.Ascending}})
in
    Ordenado'''

M_FACT_DEVOLUCIONES = '''let
    Origen = fnHoja("Fact_Devoluciones"),
    Renombrado = Table.RenameColumns(Origen, {{"Fecha registro", "Fecha Registro"}, {"# Pedido", "Pedido"}, {"# Factura", "Factura"}, {"# Planilla", "Planilla"}, {"Cód. producto", "Código Producto"}, {"Descripción producto", "Descripción Producto"}, {"Und. empaque", "Unidad Empaque"}, {"Peso unit. (KG)", "Peso Unitario KG"}, {"Cant. devuelta", "Cantidad Devuelta"}, {"Peso devuelto (KG)", "Peso Devuelto KG"}, {"Valor unitario", "Valor Unitario"}, {"Valor devolución", "Valor Devolución"}, {"Motivo devolución", "Motivo Devolución"}, {"Fecha despacho", "Fecha Despacho"}, {"Fecha recep. bodega", "Fecha Recepción Bodega"}, {"# Nota crédito", "Nota Crédito"}, {"Fecha nota crédito", "Fecha Nota Crédito"}, {"Días de gestión", "Días de Gestión"}}),
    NoNulos = Table.SelectRows(Renombrado, each [Consecutivo] <> null),
    Tipos = Table.TransformColumnTypes(NoNulos, {{"Consecutivo", Int64.Type}, {"Fecha Registro", type date}, {"Pedido", Int64.Type}, {"Factura", Int64.Type}, {"Planilla", Int64.Type}, {"Cliente", type text}, {"Código SN", type text}, {"Ciudad", type text}, {"Vendedor", type text}, {"Ruta", type text}, {"Transportadora", type text}, {"Transportador", type text}, {"Placa", type text}, {"Fecha Despacho", type date}, {"Código Producto", type text}, {"Descripción Producto", type text}, {"Unidad Empaque", type text}, {"Peso Unitario KG", type number}, {"Cantidad Devuelta", type number}, {"Peso Devuelto KG", type number}, {"Valor Unitario", type number}, {"Valor Devolución", type number}, {"Motivo Devolución", type text}, {"Estado", type text}, {"Fecha Recepción Bodega", type date}, {"Nota Crédito", type text}, {"Fecha Nota Crédito", type date}, {"Días de Gestión", Int64.Type}, {"Responsable", type text}, {"Observaciones", type text}}),
    ConKey = Table.AddColumn(Tipos, "ClienteKey", each if [Cliente] = null then null else Text.Upper(Text.Trim([Cliente])), type text),
    Final = Table.SelectColumns(ConKey, {"Consecutivo", "Fecha Registro", "Planilla", "Pedido", "Factura", "Cliente", "ClienteKey", "Código SN", "Ciudad", "Vendedor", "Ruta", "Transportadora", "Transportador", "Placa", "Fecha Despacho", "Código Producto", "Descripción Producto", "Unidad Empaque", "Peso Unitario KG", "Cantidad Devuelta", "Peso Devuelto KG", "Valor Unitario", "Valor Devolución", "Motivo Devolución", "Estado", "Fecha Recepción Bodega", "Nota Crédito", "Fecha Nota Crédito", "Días de Gestión", "Responsable", "Observaciones"})
in
    Final'''

M_MEDIDAS = '''let
    Origen = Table.FromRows({{"Medidas"}}, {"Grupo"}),
    Tipos = Table.TransformColumnTypes(Origen, {{"Grupo", type text}})
in
    Tipos'''
