import { createHash } from 'node:crypto';

/**
 * Abreviaturas y variantes de nomenclatura vial colombiana. Nominatim indexa
 * las vias con el nombre largo ("Calle", "Carrera", "Avenida"), mientras que el
 * Excel de despacho suele traer "CLL", "CRA", "KR", "AV". Sin esta expansion la
 * tasa de aciertos cae drasticamente.
 */
const ROAD_ABBREVIATIONS: Array<[RegExp, string]> = [
  [/\b(CL|CLL|CLE|CALL)\b\.?/g, 'CALLE'],
  [/\b(CR|CRA|KR|KRA|CARR|CVA)\b\.?/g, 'CARRERA'],
  [/\b(AV|AVDA|AVEN)\b\.?/g, 'AVENIDA'],
  [/\b(DG|DIAG)\b\.?/g, 'DIAGONAL'],
  [/\b(TV|TRANSV|TRV)\b\.?/g, 'TRANSVERSAL'],
  [/\b(AUT|AUTOP)\b\.?/g, 'AUTOPISTA'],
  [/\b(MZ|MZA)\b\.?/g, 'MANZANA'],
  [/\bBRR?\b\.?/g, 'BARRIO'],
  [/\b(KM|K\.M)\b\.?/g, 'KILOMETRO'],
  [/\bVDA\b\.?/g, 'VEREDA'],
];

/**
 * Ruido que confunde al geocodificador: numeros de bodega, interiores, torres,
 * apartamentos y referencias libres. Nominatim no los resuelve y ademas hacen
 * que dos direcciones identicas generen dos entradas distintas en el cache.
 */
const NOISE_PATTERNS: RegExp[] = [
  /\b(BODEGA|BG|LOCAL|LC|OFICINA|OF|APTO|APARTAMENTO|TORRE|INT|INTERIOR|PISO|ETAPA|CONJUNTO|EDIFICIO|ED)\b[\s.#-]*[\w-]*/g,
  /\bC\.?\s*C\.?\s+[A-Z\s]+$/g,
  /\b(FRENTE A|AL LADO DE|CERCA DE|DETRAS DE|VIA A)\b.*/g,
  /\bPBX\b.*/g,
  /\bTEL[EF]?\.?\s*\d[\d\s-]*/g,
];

export interface NormalizedAddress {
  /** Cadena que efectivamente se envia a Nominatim. */
  query: string;
  /** Clave de cache (sha256 de `query`). */
  hash: string;
  /** Direccion normalizada sin el sufijo de localidad/pais. */
  street: string;
  locality?: string;
}

const stripAccents = (value: string): string =>
  value.normalize('NFD').replace(/[\u0300-\u036f]/g, '');

/**
 * Convierte "Cra 68 # 24-35 Bodega 4" + "Bogota" en
 * "CARRERA 68 24-35, BOGOTA, COLOMBIA" de forma determinista.
 *
 * El determinismo es lo que hace que el cache funcione: dos filas del Excel
 * escritas distinto pero que apuntan al mismo sitio producen el mismo hash y,
 * por lo tanto, una sola peticion a Nominatim.
 */
export function normalizeAddress(
  rawAddress: string,
  rawLocality?: string | null,
  countrySuffix = 'Colombia',
): NormalizedAddress {
  let street = stripAccents(String(rawAddress ?? '')).toUpperCase();

  // Unifica separadores de numeracion: "#", "No.", "N°", "Nro" -> espacio.
  street = street
    .replace(/[#º°]/g, ' ')
    .replace(/\bN(O|RO|UM)?\.?\b/g, ' ')
    .replace(/[.,;:]/g, ' ');

  for (const [pattern, replacement] of ROAD_ABBREVIATIONS) {
    street = street.replace(pattern, replacement);
  }
  for (const pattern of NOISE_PATTERNS) {
    street = street.replace(pattern, ' ');
  }

  street = street
    .replace(/\s*-\s*/g, '-')
    .replace(/\s+/g, ' ')
    .trim();

  const locality = rawLocality
    ? stripAccents(String(rawLocality)).toUpperCase().replace(/\s+/g, ' ').trim()
    : undefined;

  // Se agrega "Colombia" a la busqueda tal como exige el flujo de despacho.
  const query = [street, locality, countrySuffix.toUpperCase()]
    .filter((part) => part && part.length > 0)
    .join(', ');

  return {
    query,
    hash: createHash('sha256').update(query).digest('hex'),
    street,
    locality,
  };
}

/**
 * Heuristica de confianza. Nominatim devuelve `importance` y `place_rank`; una
 * respuesta que solo acerto al municipio (place_rank <= 16) no sirve para
 * enrutar un camion, asi que se marca LOW_CONFIDENCE y queda visible en el
 * dashboard para correccion manual.
 */
export function scoreResult(placeRank?: number, importance?: number, osmClass?: string): number {
  let score = importance ?? 0.2;
  if (typeof placeRank === 'number') {
    if (placeRank >= 30) score += 0.5; // numero de casa / edificio
    else if (placeRank >= 26) score += 0.3; // via con numeracion
    else if (placeRank >= 20) score += 0.1; // via
    else score -= 0.25; // solo ciudad o region
  }
  if (osmClass === 'place' || osmClass === 'boundary') score -= 0.1;
  return Math.max(0, Math.min(1, score));
}

export const LOW_CONFIDENCE_THRESHOLD = 0.35;
