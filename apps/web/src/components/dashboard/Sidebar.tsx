'use client';

import clsx from 'clsx';

const NAV = [
  { id: 'despacho', label: 'Despacho', icon: 'M3 12l2-7h14l2 7v7H3zM7 19a2 2 0 104 0 2 2 0 10-4 0M13 19a2 2 0 104 0 2 2 0 10-4 0' },
  { id: 'rutas', label: 'Rutas', icon: 'M4 19V5m0 0l6 4 4-4 6 4v10l-6-4-4 4-6-4' },
  { id: 'clientes', label: 'Clientes', icon: 'M12 12a4 4 0 100-8 4 4 0 000 8zM4 20a8 8 0 0116 0' },
  { id: 'evidencias', label: 'Evidencias', icon: 'M4 5h16v14H4zM8 11l3 3 5-5' },
  { id: 'reportes', label: 'Reportes', icon: 'M5 20V10M12 20V4M19 20v-7' },
];

export function Sidebar({ active = 'despacho' }: { active?: string }) {
  return (
    <nav
      aria-label="Navegacion principal"
      className="flex w-[76px] shrink-0 flex-col items-center gap-1 border-r border-border-subtle bg-surface-sunken py-4"
    >
      <div className="mb-4 grid h-10 w-10 place-items-center rounded-control bg-brand text-sm font-black text-content-inverse">
        CG
      </div>

      {NAV.map((item) => (
        <button
          key={item.id}
          type="button"
          aria-current={item.id === active ? 'page' : undefined}
          className={clsx(
            'group flex w-[60px] flex-col items-center gap-1 rounded-control px-1 py-2 transition-colors',
            item.id === active
              ? 'bg-brand-soft text-brand'
              : 'text-content-muted hover:bg-surface-raised hover:text-content-secondary',
          )}
        >
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
            <path d={item.icon} />
          </svg>
          <span className="text-[10px] font-medium leading-none">{item.label}</span>
        </button>
      ))}
    </nav>
  );
}
