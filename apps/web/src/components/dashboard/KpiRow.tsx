'use client';

import { formatKg, formatNumber, formatPercent } from '@/lib/format';
import type { DashboardSummary } from '@/types/tms';

interface KpiRowProps {
  summary: DashboardSummary | undefined;
}

export function KpiRow({ summary }: KpiRowProps) {
  const cards = [
    { label: 'Rutas del dia', value: summary ? formatNumber(summary.routes) : '—' },
    { label: 'Entregas', value: summary ? formatNumber(summary.orders) : '—' },
    {
      label: 'Completadas',
      value: summary ? `${formatNumber(summary.delivered)} · ${formatPercent(summary.completionRate)}` : '—',
      token: 'var(--status-delivered)',
    },
    { label: 'En ruta', value: summary ? formatNumber(summary.inTransit) : '—', token: 'var(--status-transit)' },
    {
      label: 'Novedades',
      value: summary ? formatNumber(summary.failed) : '—',
      token: summary && summary.failed > 0 ? 'var(--status-failed)' : undefined,
    },
    { label: 'Peso despachado', value: summary ? formatKg(summary.totalWeightKg) : '—' },
    {
      label: 'Sin ubicar',
      value: summary ? formatNumber(summary.pendingGeocode) : '—',
      token: summary && summary.pendingGeocode > 0 ? 'var(--status-warning)' : undefined,
    },
  ];

  return (
    <div className="grid grid-cols-2 gap-3 px-6 py-4 sm:grid-cols-4 xl:grid-cols-7">
      {cards.map((card) => (
        <div key={card.label} className="card px-4 py-3">
          <p className="text-[10px] font-semibold uppercase tracking-wider text-content-muted">
            {card.label}
          </p>
          <p
            className="mt-1 text-lg font-semibold leading-tight text-content-primary"
            style={card.token ? { color: card.token } : undefined}
          >
            {card.value}
          </p>
        </div>
      ))}
    </div>
  );
}
