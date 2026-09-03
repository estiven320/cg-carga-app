const numberFormatter = new Intl.NumberFormat('es-CO', { maximumFractionDigits: 1 });
const integerFormatter = new Intl.NumberFormat('es-CO', { maximumFractionDigits: 0 });

export const formatKg = (value: number): string => `${numberFormatter.format(value)} kg`;
export const formatNumber = (value: number): string => integerFormatter.format(value);
export const formatPercent = (value: number): string => `${Math.round(value * 100)}%`;

export const formatTimeWindow = (start: string | null, end: string | null): string | null => {
  if (!start && !end) return null;
  if (start && end && start === end) return `Cita ${start}`;
  if (start && end) return `${start} – ${end}`;
  if (end) return `Antes de ${end}`;
  return `Desde ${start}`;
};

/** "2026-09-03" para el input date y para los parametros del API. */
export const toDateInput = (date: Date): string => date.toISOString().slice(0, 10);

export const formatDateLong = (iso: string): string =>
  new Date(`${iso}T12:00:00Z`).toLocaleDateString('es-CO', {
    weekday: 'long',
    day: 'numeric',
    month: 'long',
    year: 'numeric',
  });

export const formatEta = (ms: number): string => {
  const minutes = Math.round(ms / 60_000);
  if (minutes < 1) return 'menos de 1 min';
  if (minutes < 60) return `${minutes} min`;
  return `${Math.floor(minutes / 60)} h ${minutes % 60} min`;
};
