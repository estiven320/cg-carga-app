export interface TimeWindow {
  start: string | null; // "HH:mm"
  end: string | null;
  requiresAppointment: boolean;
}

/**
 * Extrae ventanas horarias del texto libre de `COMENTARIOS + TENER EN CUENTA`.
 *
 * El area comercial escribe estas restricciones en lenguaje natural y son la
 * causa numero uno de reentregas. Ejemplos reales que este parser cubre:
 *   "ENTREGAR DE 8:00 A 12:00"        -> 08:00 - 12:00
 *   "RECIBEN DE 7 AM A 3 PM"          -> 07:00 - 15:00
 *   "SOLO ANTES DE LAS 11"            ->   null - 11:00
 *   "DESPUES DE LA 1 PM"              -> 13:00 - null
 *   "CITA 10:30"                      -> 10:30 - 10:30, requiresAppointment
 *   "HORARIO 6AM-2PM / AGENDAR CITA"  -> 06:00 - 14:00, requiresAppointment
 *
 * Lo que no reconoce queda como null: el comentario crudo sigue visible en el
 * dashboard y en la app del conductor, nunca se pierde informacion.
 */
const APPOINTMENT_HINTS = /\b(CITA|AGENDA|AGENDAR|PROGRAMAR ENTREGA|TURNO|RESERVA)\b/;

const pad = (n: number): string => String(n).padStart(2, '0');

/** Convierte hora + minuto + meridiano a "HH:mm" en formato 24 h. */
function toHHmm(hour: number, minute: number, meridiem?: string | null): string | null {
  let h = hour;
  const m = minute;
  if (Number.isNaN(h) || h < 0 || h > 24 || m < 0 || m > 59) return null;

  const mer = meridiem?.toUpperCase().replace(/\./g, '');
  if (mer === 'PM' && h < 12) h += 12;
  if (mer === 'AM' && h === 12) h = 0;

  // Sin meridiano explicito se aplica el horario laboral colombiano: una hora
  // entre 1 y 6 casi siempre significa la tarde en un contexto de entregas.
  if (!mer && h >= 1 && h <= 6) h += 12;

  if (h === 24) h = 0;
  return `${pad(h)}:${pad(m)}`;
}

const HOUR = String.raw`(\d{1,2})(?:[:.\s](\d{2}))?\s*(A\.?M\.?|P\.?M\.?|AM|PM)?`;

const RANGE_PATTERNS = [
  new RegExp(String.raw`(?:DE|ENTRE|HORARIO|ENTREGAR|RECIBEN?|ATIENDEN?)?\s*${HOUR}\s*(?:A|HASTA|-|–|Y)\s*${HOUR}`, 'i'),
];

const BEFORE_PATTERNS = [
  new RegExp(String.raw`(?:ANTES DE(?: LAS?)?|HASTA(?: LAS?)?|MAXIMO(?: A)?(?: LAS?)?|LIMITE)\s*${HOUR}`, 'i'),
];

const AFTER_PATTERNS = [
  new RegExp(String.raw`(?:DESPUES DE(?: LAS?)?|A PARTIR DE(?: LAS?)?|DESDE(?: LAS?)?)\s*${HOUR}`, 'i'),
];

const APPOINTMENT_TIME = new RegExp(String.raw`\b(?:CITA|TURNO)\s*(?:A(?: LAS?)?)?\s*${HOUR}`, 'i');

export function parseTimeWindow(rawComment?: string | null): TimeWindow {
  const empty: TimeWindow = { start: null, end: null, requiresAppointment: false };
  if (!rawComment) return empty;

  const text = String(rawComment)
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .toUpperCase()
    .replace(/\s+/g, ' ');

  const requiresAppointment = APPOINTMENT_HINTS.test(text);

  for (const pattern of RANGE_PATTERNS) {
    const match = text.match(pattern);
    if (match) {
      const [, h1, m1, mer1, h2, m2, mer2] = match;
      // "8 A 12 PM": el meridiano del final tambien aplica al inicio si el
      // rango quedaria invertido.
      let start = toHHmm(Number(h1), Number(m1 ?? 0), mer1 ?? null);
      const end = toHHmm(Number(h2), Number(m2 ?? 0), mer2 ?? null);
      if (start && end && start > end && !mer1 && mer2) {
        start = toHHmm(Number(h1), Number(m1 ?? 0), 'AM');
      }
      if (start && end && start <= end) return { start, end, requiresAppointment };
    }
  }

  const appointment = text.match(APPOINTMENT_TIME);
  if (appointment) {
    const [, h, m, mer] = appointment;
    const at = toHHmm(Number(h), Number(m ?? 0), mer ?? null);
    if (at) return { start: at, end: at, requiresAppointment: true };
  }

  for (const pattern of BEFORE_PATTERNS) {
    const match = text.match(pattern);
    if (match) {
      const [, h, m, mer] = match;
      const end = toHHmm(Number(h), Number(m ?? 0), mer ?? null);
      if (end) return { start: null, end, requiresAppointment };
    }
  }

  for (const pattern of AFTER_PATTERNS) {
    const match = text.match(pattern);
    if (match) {
      const [, h, m, mer] = match;
      const start = toHHmm(Number(h), Number(m ?? 0), mer ?? null);
      if (start) return { start, end: null, requiresAppointment };
    }
  }

  return { start: null, end: null, requiresAppointment };
}
