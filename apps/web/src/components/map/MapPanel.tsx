'use client';

import dynamic from 'next/dynamic';
import { useMemo } from 'react';
import type { DeliveryMapProps } from './DeliveryMap';
import type { Route } from '@/types/tms';

/**
 * Leaflet toca `window` al importarse, asi que el mapa NO puede renderizarse en
 * el servidor. Este wrapper lo carga solo en cliente y muestra un esqueleto
 * mientras llega el bundle.
 */
const DeliveryMap = dynamic(() => import('./DeliveryMap'), {
  ssr: false,
  loading: () => (
    <div className="grid h-full w-full place-items-center bg-surface-sunken">
      <div className="flex flex-col items-center gap-3 text-content-muted">
        <div className="h-8 w-8 animate-spin rounded-full border-2 border-border-strong border-t-brand" />
        <p className="text-xs">Cargando mapa de OpenStreetMap…</p>
      </div>
    </div>
  ),
});

interface MapPanelProps extends DeliveryMapProps {
  routes: Route[];
  pendingGeocode: number;
}

export function MapPanel({ pendingGeocode, ...mapProps }: MapPanelProps) {
  const legend = useMemo(
    () =>
      (mapProps.visibleRouteIds.length === 0
        ? mapProps.routes
        : mapProps.routes.filter((route) => mapProps.visibleRouteIds.includes(route.id))
      ).slice(0, 12),
    [mapProps.routes, mapProps.visibleRouteIds],
  );

  return (
    <div className="relative h-full w-full overflow-hidden">
      <DeliveryMap {...mapProps} />

      {/* Leyenda de rutas: el color del pin es la unica forma de leer el mapa
          de un vistazo, asi que la correspondencia color -> N/RUTA es fija. */}
      <div className="pointer-events-none absolute bottom-6 left-4 z-[1000] max-w-[240px]">
        <div className="pointer-events-auto card p-3">
          <p className="mb-2 text-[10px] font-semibold uppercase tracking-wider text-content-muted">
            Rutas en el mapa
          </p>
          <ul className="space-y-1.5">
            {legend.map((route) => (
              <li key={route.id} className="flex items-center gap-2 text-xs">
                <span
                  className="h-2.5 w-2.5 shrink-0 rounded-full"
                  style={{ background: route.color }}
                  aria-hidden
                />
                <span className="font-medium text-content-primary">Ruta {route.code}</span>
                <span className="ml-auto text-content-muted">
                  {route.deliveredCount}/{route.totalOrders}
                </span>
              </li>
            ))}
          </ul>
        </div>
      </div>

      {pendingGeocode > 0 && (
        <div className="absolute right-4 top-4 z-[1000] card border-status-warning/40 px-3 py-2">
          <p className="text-xs font-medium text-status-warning">
            {pendingGeocode} direccion{pendingGeocode === 1 ? '' : 'es'} sin ubicar
          </p>
          <p className="text-[10px] text-content-muted">No aparecen en el mapa</p>
        </div>
      )}
    </div>
  );
}
