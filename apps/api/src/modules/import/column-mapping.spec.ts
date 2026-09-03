import { mapColumns } from './column-mapping';

describe('mapColumns', () => {
  const HEADERS = [
    'Número de documento',
    'Nombre de cliente/proveedor',
    'Direccion',
    'Localidad / Municipio',
    'N/RUTA',
    'Peso Kg',
    'Unidades',
    'Items',
    'COMENTARIOS + TENER EN CUENTA',
  ];

  it('mapea los encabezados exactos del archivo de despacho', () => {
    const { mapping, missingRequired } = mapColumns(HEADERS);
    expect(missingRequired).toEqual([]);
    expect(mapping).toEqual({
      documentNumber: 1,
      clientName: 2,
      address: 3,
      locality: 4,
      routeCode: 5,
      weightKg: 6,
      units: 7,
      items: 8,
      comments: 9,
    });
  });

  it('tolera tildes, mayusculas, saltos de linea y espacios dobles', () => {
    const { mapping, missingRequired } = mapColumns([
      'NUMERO  DE DOCUMENTO',
      'nombre de cliente\nproveedor',
      'DIRECCIÓN',
      'localidad/municipio',
      'N RUTA',
      'PESO (KG)',
      'UND',
      'ITEMS',
      'OBSERVACIONES',
    ]);
    expect(missingRequired).toEqual([]);
    expect(mapping.routeCode).toBe(5);
    expect(mapping.address).toBe(3);
  });

  it('reporta las columnas obligatorias ausentes', () => {
    const { missingRequired } = mapColumns(['Peso Kg', 'Unidades']);
    expect(missingRequired).toContain('Número de documento');
    expect(missingRequired).toContain('N/RUTA');
  });
});
