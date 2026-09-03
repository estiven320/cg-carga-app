'use client';

import clsx from 'clsx';
import { useState } from 'react';
import { formatKg, formatTimeWindow } from '@/lib/format';
import { GEOCODE_STATUS_META, NEEDS_ATTENTION, ORDER_STATUS_META } from '@/lib/status';
import type { Order, Route } from '@/types/tms';

interface RoutePanelProps {
  routes: Route[];
  visibleRouteIds: string[];
  onToggleRoute: (routeId: string) => void;
  onShowAll: () => void;
  selectedOrderId: string | null;
  onSelectOrder: (orderId: string) => void;
  onSendWhatsapp: (routeId: string) => void;
  query: string;
}

/**
 * Panel lateral: la lista de rutas es el indice del mapa. Cada ruta se pinta
 * con su color de `N/RUTA` para que la lista y los pines se lean como una sola
 * cosa.
 */
export function RoutePanel({
  routes,
  visibleRouteIds,
  onToggleRoute,
  onShowAll,
  selectedOrderId,
  onSelectOrder,
  onSendWhatsapp,
  query,
}: RoutePanelProps) {
  const [expanded, setExpanded] = useState<string | null>(routes[0]?.id ?? null);
  const filter = query.trim().toLowerCase();

  const matches = (order: Order): boolean =>
    !filter ||
    order.clientNameRaw.toLowerCase().includes(filter) ||
    order.documentNumber.toLowerCase().includes(filter) ||
    order.address.toLowerCase().includes(filter) ||
    (order.locality ?? '').toLowerCase().includes(filter);

  return (
    <aside className="flex w-[380px] shrink-0 flex-col border-r border-border-subtle bg-surface-raised">
      <div className="flex items-center justify-between border-b border-border-subtle px-4 py-3">
        <h2 className="text-sm font-semibold text-content-primary">
          Rutas <span className="text-content-muted">({routes.length})</span>
        </h2>
        <button
          type="button"
          className="text-xs font-medium text-brand hover:underline disabled:text-content-muted disabled:no-underline"
          onClick={onShowAll}
          disabled={visibleRouteIds.length === 0}
        >
          Ver todas
        </button>
      </div>

      <div className="flex-1 overflow-y-auto">
        {routes.length === 0 && (
          <p className="px-4 py-8 text-center text-xs text-content-muted">
            No hay rutas para esta fecha. Importa la programacion del dia.
          </p>
        )}

        {routes.map((route) => {
          const isVisible = visibleRouteIds.length === 0 || visibleRouteIds.includes(route.id);
          const isOpen = expanded === route.id;
          const visibleOrders = route.orders.filter(matches);
          const progress = route.totalOrders > 0 ? route.deliveredCount / route.totalOrders : 0;
          const attention = route.orders.filter((order) =>
            NEEDS_ATTENTION.includes(order.geocodeStatus),
          ).length;

          if (filter && visibleOrders.length === 0) return null;

          return (
            <section key={route.id} className="border-b border-border-subtle">
              <div
                className={clsx(
                  'flex items-start gap-3 px-4 py-3 transition-colors',
                  isVisible ? 'bg-transparent' : 'opacity-45',
                )}
              >
                <button
                  type="button"
                  onClick={() => onToggleRoute(route.id)}
                  className="mt-1 h-3.5 w-3.5 shrink-0 rounded-sm ring-offset-2 ring-offset-surface-raised focus:outline-none focus:ring-2 focus:ring-brand"
                  style={{ background: route.color }}
                  aria-pressed={isVisible}
                  aria-label={`${isVisible ? 'Ocultar' : 'Mostrar'} ruta ${route.code} en el mapa`}
                />

                <button
                  type="button"
                  className="min-w-0 flex-1 text-left"
                  onClick={() => setExpanded(isOpen ? null : route.id)}
                  aria-expanded={isOpen}
                >
                  <div className="flex items-baseline gap-2">
                    <span className="text-sm font-semibold text-content-primary">Ruta {route.code}</span>
                    <span className="text-[11px] text-content-muted">
                      {route.totalOrders} paradas · {formatKg(route.totalWeightKg)}
                    </span>
                  </div>

                  <p className="mt-0.5 truncate text-[11px] text-content-secondary">
                    {route.driver ? `${route.driver.fullName} · ${route.driver.vehiclePlate ?? 's/placa'}` : 'Sin conductor asignado'}
                  </p>

                  <div className="mt-2 h-1 overflow-hidden rounded-full bg-surface-sunken">
                    <div
                      className="h-full rounded-full transition-[width]"
                      style={{ width: `${progress * 100}%`, background: route.color }}
                    />
                  </div>

                  <div className="mt-1.5 flex items-center gap-3 text-[10px] text-content-muted">
                    <span>{route.deliveredCount} entregadas</span>
                    {route.failedCount > 0 && (
                      <span className="text-status-failed">{route.failedCount} fallidas</span>
                    )}
                    {attention > 0 && (
                      <span className="text-status-warning">{attention} sin ubicar</span>
                    )}
                  </div>
                </button>

                <button
                  type="button"
                  onClick={() => onSendWhatsapp(route.id)}
                  disabled={!route.driver}
                  title={route.driver ? 'Enviar ruta por WhatsApp' : 'Asigna un conductor primero'}
                  className="mt-0.5 grid h-7 w-7 shrink-0 place-items-center rounded-control text-content-muted transition-colors hover:bg-surface-overlay hover:text-status-delivered disabled:opacity-30 disabled:hover:bg-transparent"
                >
                  <svg width="15" height="15" viewBox="0 0 24 24" fill="currentColor" aria-hidden>
                    <path d="M12 2a10 10 0 00-8.6 15L2 22l5.2-1.4A10 10 0 1012 2zm5.6 14.2c-.2.6-1.2 1.2-1.7 1.2-.4 0-1 .1-3.3-.9-2.8-1.2-4.5-4-4.6-4.2-.1-.2-1.1-1.4-1.1-2.7s.7-1.9 1-2.1c.2-.3.5-.3.7-.3h.5c.2 0 .4 0 .6.5l.8 2c.1.2.1.4 0 .5l-.4.5-.3.3c-.1.2-.3.3-.1.6.2.3.8 1.3 1.7 2.1 1.2 1 2.1 1.3 2.4 1.5.3.1.4.1.6-.1l.9-1c.2-.2.3-.2.6-.1l1.9.9c.3.1.5.2.6.3.1.2.1.7-.1 1.3z" />
                  </svg>
                </button>
              </div>

              {isOpen && (
                <ul className="bg-surface-sunken/60 pb-1">
                  {visibleOrders.map((order, index) => (
                    <OrderRow
                      key={order.id}
                      order={order}
                      index={index}
                      color={route.color}
                      selected={order.id === selectedOrderId}
                      onSelect={() => onSelectOrder(order.id)}
                    />
                  ))}
                </ul>
              )}
            </section>
          );
        })}
      </div>
    </aside>
  );
}

function OrderRow({
  order,
  index,
  color,
  selected,
  onSelect,
}: {
  order: Order;
  index: number;
  color: string;
  selected: boolean;
  onSelect: () => void;
}) {
  const status = ORDER_STATUS_META[order.status];
  const geocode = GEOCODE_STATUS_META[order.geocodeStatus];
  const timeWindow = formatTimeWindow(order.timeWindowStart, order.timeWindowEnd);
  const needsAttention = NEEDS_ATTENTION.includes(order.geocodeStatus);

  return (
    <li>
      <button
        type="button"
        onClick={onSelect}
        className={clsx(
          'flex w-full items-start gap-3 px-4 py-2.5 text-left transition-colors',
          selected ? 'bg-brand-soft' : 'hover:bg-surface-overlay',
        )}
      >
        <span
          className="mt-0.5 grid h-5 w-5 shrink-0 place-items-center rounded-full text-[10px] font-bold text-[#0b1017]"
          style={{ background: color }}
        >
          {order.sequence ?? index + 1}
        </span>

        <span className="min-w-0 flex-1">
          <span className="flex items-center gap-2">
            <span className="truncate text-xs font-medium text-content-primary">
              {order.clientNameRaw}
            </span>
            {order.requiresAppointment && (
              <span className="shrink-0 rounded bg-status-warning/15 px-1 text-[9px] font-bold uppercase text-status-warning">
                cita
              </span>
            )}
          </span>

          <span className="mt-0.5 block truncate text-[11px] text-content-muted">
            {order.address}
            {order.locality ? `, ${order.locality}` : ''}
          </span>

          <span className="mt-1 flex flex-wrap items-center gap-x-3 gap-y-0.5 text-[10px]">
            <span style={{ color: status.token }}>{status.label}</span>
            {timeWindow && <span className="text-content-secondary">{timeWindow}</span>}
            <span className="text-content-muted">{formatKg(order.weightKg)}</span>
            {order.proofCount > 0 && (
              <span className="text-status-delivered">{order.proofCount} foto(s)</span>
            )}
            {needsAttention && <span style={{ color: geocode.token }}>{geocode.label}</span>}
          </span>
        </span>
      </button>
    </li>
  );
}
