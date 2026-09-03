'use client';

import clsx from 'clsx';
import { formatDateLong } from '@/lib/format';

interface TopbarProps {
  date: string;
  onDateChange: (date: string) => void;
  query: string;
  onQueryChange: (query: string) => void;
  connected: boolean;
  onImport: () => void;
  onRefresh: () => void;
}

export function Topbar({
  date,
  onDateChange,
  query,
  onQueryChange,
  connected,
  onImport,
  onRefresh,
}: TopbarProps) {
  return (
    <header className="flex items-center gap-4 border-b border-border-subtle bg-surface-raised px-6 py-3">
      <div className="min-w-0">
        <h1 className="text-base font-semibold leading-tight text-content-primary">Control de entregas</h1>
        <p className="truncate text-xs capitalize text-content-muted">{formatDateLong(date)}</p>
      </div>

      <div className="relative ml-6 w-full max-w-sm">
        <svg
          className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-content-muted"
          width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden
        >
          <circle cx="11" cy="11" r="7" />
          <path d="m20 20-3.5-3.5" strokeLinecap="round" />
        </svg>
        <input
          className="input pl-9"
          placeholder="Buscar cliente, documento o direccion…"
          value={query}
          onChange={(event) => onQueryChange(event.target.value)}
          aria-label="Buscar entregas"
        />
      </div>

      <div className="ml-auto flex items-center gap-3">
        <span
          className={clsx(
            'flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-[11px] font-medium',
            connected
              ? 'border-status-delivered/30 text-status-delivered'
              : 'border-border-subtle text-content-muted',
          )}
          title={connected ? 'Recibiendo actualizaciones en vivo' : 'Sin conexion en vivo; se refresca cada minuto'}
        >
          <span
            className={clsx('h-1.5 w-1.5 rounded-full', connected ? 'bg-status-delivered' : 'bg-content-muted')}
          />
          {connected ? 'En vivo' : 'Desconectado'}
        </span>

        <input
          type="date"
          className="input w-[150px]"
          value={date}
          onChange={(event) => onDateChange(event.target.value)}
          aria-label="Fecha de despacho"
        />

        <button type="button" className="btn-ghost" onClick={onRefresh}>
          Actualizar
        </button>
        <button type="button" className="btn-primary" onClick={onImport}>
          Importar programacion
        </button>
      </div>
    </header>
  );
}
