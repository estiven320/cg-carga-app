'use client';

import { useCallback, useMemo, useState } from 'react';
import { GeocodeProgress } from '@/components/dashboard/GeocodeProgress';
import { ImportDialog } from '@/components/dashboard/ImportDialog';
import { KpiRow } from '@/components/dashboard/KpiRow';
import { RoutePanel } from '@/components/dashboard/RoutePanel';
import { Sidebar } from '@/components/dashboard/Sidebar';
import { Topbar } from '@/components/dashboard/Topbar';
import { MapPanel } from '@/components/map/MapPanel';
import { useDispatchData } from '@/hooks/useDispatchData';
import { useRealtime } from '@/hooks/useRealtime';
import { api } from '@/lib/api';
import { toDateInput } from '@/lib/format';
import type { Driver } from '@/types/tms';

const DEFAULT_SHEET = 'PROGRAMACION 3 DE SEPTIEMBRE';

/**
 * Dashboard de despacho.
 *
 * Disposicion en tres zonas, que es como trabaja realmente un despachador:
 *   - izquierda: rutas y paradas (el indice),
 *   - centro: mapa de Leaflet con los pines por `N/RUTA` (el estado del dia),
 *   - arriba: KPIs, busqueda y la accion de importar (el control).
 */
export default function DispatchDashboard() {
  const [date, setDate] = useState(() => toDateInput(new Date()));
  const [query, setQuery] = useState('');
  const [visibleRouteIds, setVisibleRouteIds] = useState<string[]>([]);
  const [selectedOrderId, setSelectedOrderId] = useState<string | null>(null);
  const [importOpen, setImportOpen] = useState(false);
  const [toast, setToast] = useState<string | null>(null);

  const { routes, summary, isLoading, refresh } = useDispatchData(date);

  // Cualquier evento del backend (entrega registrada, direccion geocodificada,
  // ping del conductor) revalida los datos del dia.
  const { connected, importProgress, driverPositions } = useRealtime(
    useCallback(() => refresh(), [refresh]),
  );

  /** Conductores con su ultima posicion: la del socket manda sobre la de la BD. */
  const drivers = useMemo<Array<Driver & { routeColor: string }>>(
    () =>
      routes
        .filter((route) => route.driver)
        .map((route) => {
          const live = driverPositions[route.driver!.id];
          return {
            ...route.driver!,
            lastLat: live?.lat ?? route.driver!.lastLat,
            lastLng: live?.lng ?? route.driver!.lastLng,
            lastPingAt: live?.recordedAt ?? route.driver!.lastPingAt,
            routeColor: route.color,
          };
        }),
    [routes, driverPositions],
  );

  const toggleRoute = (routeId: string) => {
    setVisibleRouteIds((current) => {
      // Vacio significa "todas": el primer clic aisla la ruta elegida.
      if (current.length === 0) return routes.filter((route) => route.id !== routeId).map((route) => route.id);
      const next = current.includes(routeId)
        ? current.filter((id) => id !== routeId)
        : [...current, routeId];
      return next.length === routes.length ? [] : next;
    });
  };

  const moveOrder = async (orderId: string, lat: number, lng: number) => {
    try {
      await api.setCoordinates(orderId, lat, lng);
      setToast('Ubicacion corregida');
      refresh();
    } catch {
      setToast('No se pudo guardar la ubicacion');
    }
  };

  const sendWhatsapp = async (routeId: string) => {
    try {
      await api.sendRouteWhatsapp(routeId);
      setToast('Ruta enviada al conductor por WhatsApp');
    } catch {
      setToast('No se pudo enviar la ruta');
    }
  };

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-surface-base">
      <Sidebar active="despacho" />

      <div className="flex min-w-0 flex-1 flex-col">
        <Topbar
          date={date}
          onDateChange={setDate}
          query={query}
          onQueryChange={setQuery}
          connected={connected}
          onImport={() => setImportOpen(true)}
          onRefresh={refresh}
        />

        <GeocodeProgress progress={importProgress} />
        <KpiRow summary={summary} />

        <main className="flex min-h-0 flex-1 border-t border-border-subtle">
          <RoutePanel
            routes={routes}
            visibleRouteIds={visibleRouteIds}
            onToggleRoute={toggleRoute}
            onShowAll={() => setVisibleRouteIds([])}
            selectedOrderId={selectedOrderId}
            onSelectOrder={setSelectedOrderId}
            onSendWhatsapp={sendWhatsapp}
            query={query}
          />

          <div className="relative min-w-0 flex-1">
            {isLoading && routes.length === 0 ? (
              <div className="grid h-full place-items-center text-xs text-content-muted">
                Cargando programacion…
              </div>
            ) : (
              <MapPanel
                routes={routes}
                visibleRouteIds={visibleRouteIds}
                selectedOrderId={selectedOrderId}
                onSelectOrder={setSelectedOrderId}
                onMoveOrder={moveOrder}
                drivers={drivers}
                showRouteLines
                pendingGeocode={summary?.pendingGeocode ?? 0}
              />
            )}
          </div>
        </main>
      </div>

      <ImportDialog
        open={importOpen}
        defaultSheet={DEFAULT_SHEET}
        onClose={() => {
          setImportOpen(false);
          refresh();
        }}
        onImported={(result) => setDate(result.dispatchDate.slice(0, 10))}
      />

      {toast && (
        <div
          role="status"
          className="fixed bottom-6 left-1/2 z-[3000] -translate-x-1/2 rounded-control bg-surface-overlay px-4 py-2.5 text-xs text-content-primary shadow-overlay"
          onAnimationEnd={() => setToast(null)}
        >
          {toast}
          <button
            type="button"
            className="ml-3 text-content-muted hover:text-content-primary"
            onClick={() => setToast(null)}
            aria-label="Cerrar aviso"
          >
            ×
          </button>
        </div>
      )}
    </div>
  );
}
