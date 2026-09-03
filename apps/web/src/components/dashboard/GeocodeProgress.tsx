'use client';

import { formatEta } from '@/lib/format';

interface GeocodeProgressProps {
  progress: { done: number; total: number; stage: string; etaMs?: number } | null;
}

/**
 * Barra de avance de la geocodificacion.
 *
 * Es importante mostrarla: a 1 direccion/s una programacion de 200 paradas
 * tarda mas de tres minutos, y sin retroalimentacion el despachador cree que
 * la importacion fallo.
 */
export function GeocodeProgress({ progress }: GeocodeProgressProps) {
  if (!progress || progress.total === 0) return null;

  const pct = Math.round((progress.done / progress.total) * 100);
  const label = progress.stage === 'geocoding' ? 'Ubicando direcciones' : 'Guardando ordenes';

  return (
    <div className="border-b border-border-subtle bg-surface-raised px-6 py-2.5">
      <div className="flex items-center gap-3">
        <span className="text-xs font-medium text-content-secondary">{label}</span>
        <span className="font-mono text-xs text-content-muted">
          {progress.done}/{progress.total}
        </span>
        <div className="h-1.5 flex-1 overflow-hidden rounded-full bg-surface-sunken">
          <div
            className="h-full rounded-full bg-brand transition-[width] duration-300"
            style={{ width: `${pct}%` }}
          />
        </div>
        <span className="text-xs text-content-muted">
          {progress.etaMs ? `~${formatEta(progress.etaMs)} restantes` : `${pct}%`}
        </span>
      </div>
    </div>
  );
}
