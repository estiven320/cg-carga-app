import type { GeocodeStatus, OrderStatus } from '@/types/tms';

export const ORDER_STATUS_META: Record<OrderStatus, { label: string; token: string }> = {
  PENDING: { label: 'Pendiente', token: 'var(--status-pending)' },
  ASSIGNED: { label: 'Asignada', token: 'var(--status-pending)' },
  IN_TRANSIT: { label: 'En ruta', token: 'var(--status-transit)' },
  ARRIVED: { label: 'En sitio', token: 'var(--status-transit)' },
  DELIVERED: { label: 'Entregada', token: 'var(--status-delivered)' },
  PARTIAL: { label: 'Parcial', token: 'var(--status-warning)' },
  FAILED: { label: 'Fallida', token: 'var(--status-failed)' },
  RESCHEDULED: { label: 'Reprogramada', token: 'var(--status-warning)' },
  CANCELLED: { label: 'Anulada', token: 'var(--content-muted)' },
};

export const GEOCODE_STATUS_META: Record<GeocodeStatus, { label: string; token: string }> = {
  PENDING: { label: 'Sin geocodificar', token: 'var(--status-pending)' },
  RESOLVED: { label: 'Ubicada', token: 'var(--status-delivered)' },
  LOW_CONFIDENCE: { label: 'Ubicacion dudosa', token: 'var(--status-warning)' },
  MANUAL: { label: 'Ajustada a mano', token: 'var(--status-transit)' },
  NOT_FOUND: { label: 'No encontrada', token: 'var(--status-failed)' },
  ERROR: { label: 'Error de geocodificacion', token: 'var(--status-failed)' },
};

/** Direcciones que el despachador debe revisar antes de despachar. */
export const NEEDS_ATTENTION: GeocodeStatus[] = ['PENDING', 'LOW_CONFIDENCE', 'NOT_FOUND', 'ERROR'];
