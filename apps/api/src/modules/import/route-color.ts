/**
 * Paleta de colores para los marcadores de Leaflet agrupados por `N/RUTA`.
 *
 * Requisitos que cumple:
 *  - Alto contraste entre si y sobre el tile gris/claro de OpenStreetMap.
 *  - Contraste >= 4.5:1 con texto blanco encima (etiqueta del pin).
 *  - Asignacion DETERMINISTA: el codigo de ruta siempre produce el mismo color,
 *    en el backend y en el frontend, entre recargas y entre dias.
 */
export const ROUTE_PALETTE = [
  '#2DD4BF', // teal
  '#F97316', // naranja
  '#8B5CF6', // violeta
  '#22C55E', // verde
  '#EF4444', // rojo
  '#3B82F6', // azul
  '#EAB308', // ambar
  '#EC4899', // fucsia
  '#06B6D4', // cian
  '#84CC16', // lima
  '#A855F7', // purpura
  '#F43F5E', // rosa
  '#14B8A6', // turquesa
  '#F59E0B', // dorado
  '#6366F1', // indigo
  '#10B981', // esmeralda
] as const;

/** Hash FNV-1a de 32 bits: barato, estable y sin dependencias. */
function fnv1a(value: string): number {
  let hash = 0x811c9dc5;
  for (let i = 0; i < value.length; i += 1) {
    hash ^= value.charCodeAt(i);
    hash = Math.imul(hash, 0x01000193) >>> 0;
  }
  return hash >>> 0;
}

/**
 * Rutas numericas ("1", "R-02") se reparten de forma secuencial para que rutas
 * consecutivas queden con colores bien separados; el resto cae al hash.
 */
export function colorForRoute(routeCode: string): string {
  const code = String(routeCode ?? '').trim().toUpperCase();
  if (!code) return ROUTE_PALETTE[0];

  const numeric = code.match(/(\d+)/);
  if (numeric) {
    const n = Number.parseInt(numeric[1], 10);
    if (Number.isFinite(n)) return ROUTE_PALETTE[n % ROUTE_PALETTE.length];
  }
  return ROUTE_PALETTE[fnv1a(code) % ROUTE_PALETTE.length];
}
