/**
 * Mapeo de las columnas exactas de la hoja de programacion de despacho.
 *
 * Los encabezados llegan del area operativa con variaciones inevitables:
 * tildes, mayusculas, espacios dobles, saltos de linea dentro de la celda y
 * pequenos cambios de redaccion entre semanas. Por eso NO se comparan
 * literales: cada columna declara un conjunto de alias y la coincidencia se
 * hace sobre la version normalizada del encabezado.
 */
export type OrderColumn =
  | 'documentNumber'
  | 'clientName'
  | 'address'
  | 'locality'
  | 'routeCode'
  | 'weightKg'
  | 'units'
  | 'items'
  | 'comments';

export interface ColumnSpec {
  key: OrderColumn;
  /** Encabezado canonico tal como aparece en el archivo de referencia. */
  canonical: string;
  aliases: string[];
  required: boolean;
}

export const COLUMN_SPECS: ColumnSpec[] = [
  {
    key: 'documentNumber',
    canonical: 'Número de documento',
    aliases: ['NUMERO DE DOCUMENTO', 'NO DE DOCUMENTO', 'DOCUMENTO', 'NRO DOCUMENTO', 'REMISION'],
    required: true,
  },
  {
    key: 'clientName',
    canonical: 'Nombre de cliente/proveedor',
    aliases: [
      'NOMBRE DE CLIENTE/PROVEEDOR',
      'NOMBRE DE CLIENTE PROVEEDOR',
      'NOMBRE CLIENTE/PROVEEDOR',
      'NOMBRE DEL CLIENTE',
      'CLIENTE',
      'NOMBRE CLIENTE',
    ],
    required: true,
  },
  {
    key: 'address',
    canonical: 'Direccion',
    aliases: ['DIRECCION', 'DIRECCION DE ENTREGA', 'DIR', 'DIRECCION CLIENTE'],
    required: true,
  },
  {
    key: 'locality',
    canonical: 'Localidad / Municipio',
    aliases: [
      'LOCALIDAD / MUNICIPIO',
      'LOCALIDAD/MUNICIPIO',
      'LOCALIDAD MUNICIPIO',
      'LOCALIDAD',
      'MUNICIPIO',
      'CIUDAD',
      'BARRIO/LOCALIDAD',
    ],
    required: false,
  },
  {
    key: 'routeCode',
    canonical: 'N/RUTA',
    aliases: ['N/RUTA', 'N RUTA', 'NRUTA', 'NO RUTA', 'NUMERO DE RUTA', 'RUTA'],
    required: true,
  },
  {
    key: 'weightKg',
    canonical: 'Peso Kg',
    aliases: ['PESO KG', 'PESO (KG)', 'PESO', 'KILOS', 'KG'],
    required: false,
  },
  {
    key: 'units',
    canonical: 'Unidades',
    aliases: ['UNIDADES', 'UNID', 'UND', 'CANTIDAD'],
    required: false,
  },
  {
    key: 'items',
    canonical: 'Items',
    aliases: ['ITEMS', 'ITEM', 'REFERENCIAS', 'LINEAS'],
    required: false,
  },
  {
    key: 'comments',
    canonical: 'COMENTARIOS + TENER EN CUENTA',
    aliases: [
      'COMENTARIOS + TENER EN CUENTA',
      'COMENTARIOS +TENER EN CUENTA',
      'COMENTARIOS Y TENER EN CUENTA',
      'COMENTARIOS TENER EN CUENTA',
      'COMENTARIOS',
      'OBSERVACIONES',
      'TENER EN CUENTA',
    ],
    required: false,
  },
];

export const normalizeHeader = (value: unknown): string =>
  String(value ?? '')
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .replace(/[\r\n]+/g, ' ')
    .replace(/\s+/g, ' ')
    .trim()
    .toUpperCase();

/**
 * Resuelve el indice (1-based, como ExcelJS) de cada columna a partir de la
 * fila de encabezados. Coincidencia exacta primero, luego por inclusion, para
 * tolerar encabezados como "DIRECCION DE ENTREGA (COMPLETA)".
 */
export function mapColumns(headerRow: unknown[]): {
  mapping: Partial<Record<OrderColumn, number>>;
  missingRequired: string[];
  unmapped: string[];
} {
  const normalized = headerRow.map((cell) => normalizeHeader(cell));
  const mapping: Partial<Record<OrderColumn, number>> = {};
  const used = new Set<number>();

  for (const spec of COLUMN_SPECS) {
    const candidates = [normalizeHeader(spec.canonical), ...spec.aliases.map(normalizeHeader)];

    let index = normalized.findIndex(
      (header, i) => !used.has(i) && header.length > 0 && candidates.includes(header),
    );

    if (index === -1) {
      index = normalized.findIndex(
        (header, i) =>
          !used.has(i) &&
          header.length > 0 &&
          candidates.some((candidate) => header.includes(candidate) || candidate.includes(header)),
      );
    }

    if (index !== -1) {
      used.add(index);
      mapping[spec.key] = index + 1; // ExcelJS usa columnas 1-based
    }
  }

  const missingRequired = COLUMN_SPECS.filter(
    (spec) => spec.required && mapping[spec.key] === undefined,
  ).map((spec) => spec.canonical);

  const unmapped = normalized.filter((header, i) => header.length > 0 && !used.has(i));

  return { mapping, missingRequired, unmapped };
}
