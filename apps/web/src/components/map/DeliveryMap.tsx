'use client';

import 'leaflet/dist/leaflet.css';
import L from 'leaflet';
import { Fragment, useEffect, useMemo, useRef } from 'react';
import { MapContainer, Marker, Polyline, Popup, TileLayer, useMap } from 'react-leaflet';
import type { Driver, Order, Route } from '@/types/tms';
import { formatKg, formatTimeWindow } from '@/lib/format';
import { GEOCODE_STATUS_META, ORDER_STATUS_META } from '@/lib/status';

const TILE_URL =
  process.env.NEXT_PUBLIC_TILE_URL ?? 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png';
const TILE_ATTRIBUTION =
  process.env.NEXT_PUBLIC_TILE_ATTRIBUTION ?? '&copy; Colaboradores de OpenStreetMap';
const DEFAULT_CENTER: [number, number] = [
  Number(process.env.NEXT_PUBLIC_MAP_CENTER_LAT ?? 4.6482),
  Number(process.env.NEXT_PUBLIC_MAP_CENTER_LNG ?? -74.0776),
];
const DEFAULT_ZOOM = Number(process.env.NEXT_PUBLIC_MAP_ZOOM ?? 11);

export interface DeliveryMapProps {
  routes: Route[];
  /** Ids de rutas visibles. Vacio = todas. */
  visibleRouteIds: string[];
  selectedOrderId: string | null;
  onSelectOrder: (orderId: string | null) => void;
  /** Se dispara al arrastrar un pin: corrige la coordenada geocodificada. */
  onMoveOrder?: (orderId: string, lat: number, lng: number) => void;
  drivers: Array<Driver & { routeColor: string }>;
  showRouteLines: boolean;
}

type PlacedOrder = Order & { lat: number; lng: number };

const hasCoordinates = (order: Order): order is PlacedOrder =>
  typeof order.lat === 'number' && typeof order.lng === 'number';

/**
 * Icono del marcador.
 *
 * Se usa `divIcon` en vez de imagenes porque el color proviene de `N/RUTA` y es
 * dinamico: generar un PNG por ruta seria inviable. El HTML se memoiza por
 * combinacion color+etiqueta+estado para no reconstruir cientos de iconos en
 * cada render.
 */
const iconCache = new Map<string, L.DivIcon>();

function routeIcon(color: string, label: string, status: string, selected: boolean): L.DivIcon {
  const key = `${color}|${label}|${status}|${selected}`;
  const cached = iconCache.get(key);
  if (cached) return cached;

  const statusClass =
    status === 'DELIVERED' ? ' route-pin--delivered' : status === 'FAILED' ? ' route-pin--failed' : '';

  const icon = L.divIcon({
    className: '',
    html:
      `<div class="route-pin${statusClass}${selected ? ' route-pin--selected' : ''}" ` +
      `style="background:${color}"><span>${label}</span></div>`,
    iconSize: [26, 26],
    iconAnchor: [13, 26],
    popupAnchor: [0, -24],
  });

  iconCache.set(key, icon);
  return icon;
}

const driverIcon = (color: string): L.DivIcon =>
  L.divIcon({
    className: '',
    html:
      `<div class="driver-marker" style="border-color:${color}">` +
      `<svg width="14" height="14" viewBox="0 0 24 24" fill="${color}" aria-hidden="true">` +
      `<path d="M3 13h1l2-6h9l2 4h3a1 1 0 0 1 1 1v3h-2a2.5 2.5 0 0 0-5 0H10a2.5 2.5 0 0 0-5 0H3z"/>` +
      `</svg></div>`,
    iconSize: [30, 30],
    iconAnchor: [15, 15],
  });

/**
 * Encuadre automatico.
 *
 * El refresco de datos ocurre cada 60 s y el realtime empuja cambios continuos;
 * reencuadrar en cada uno marearia al despachador. Por eso el ajuste solo se
 * dispara cuando cambia el CONJUNTO de rutas visibles (o hay una seleccion),
 * no cuando cambian los datos de las mismas paradas.
 */
function FitBounds({
  points,
  boundsKey,
  selected,
}: {
  points: Array<[number, number]>;
  boundsKey: string;
  selected: [number, number] | null;
}) {
  const map = useMap();
  const lastKey = useRef<string>('');

  useEffect(() => {
    if (selected) {
      map.flyTo(selected, Math.max(map.getZoom(), 15), { duration: 0.6 });
      return;
    }
    if (points.length === 0 || lastKey.current === boundsKey) return;
    lastKey.current = boundsKey;
    map.fitBounds(L.latLngBounds(points), { padding: [56, 56], maxZoom: 15 });
  }, [map, points, boundsKey, selected]);

  return null;
}

export default function DeliveryMap({
  routes,
  visibleRouteIds,
  selectedOrderId,
  onSelectOrder,
  onMoveOrder,
  drivers,
  showRouteLines,
}: DeliveryMapProps) {
  const visibleRoutes = useMemo(
    () =>
      visibleRouteIds.length === 0
        ? routes
        : routes.filter((route) => visibleRouteIds.includes(route.id)),
    [routes, visibleRouteIds],
  );

  const points = useMemo<Array<[number, number]>>(
    () =>
      visibleRoutes.flatMap((route) =>
        route.orders.filter(hasCoordinates).map((order) => [order.lat, order.lng] as [number, number]),
      ),
    [visibleRoutes],
  );

  const boundsKey = useMemo(
    () => `${visibleRoutes.map((route) => route.id).join(',')}::${points.length}`,
    [visibleRoutes, points.length],
  );

  const selectedPoint = useMemo<[number, number] | null>(() => {
    if (!selectedOrderId) return null;
    for (const route of routes) {
      const order = route.orders.find((candidate) => candidate.id === selectedOrderId);
      if (order && hasCoordinates(order)) return [order.lat, order.lng];
    }
    return null;
  }, [routes, selectedOrderId]);

  return (
    <MapContainer center={DEFAULT_CENTER} zoom={DEFAULT_ZOOM} zoomControl className="h-full w-full">
      {/* Tiles de OpenStreetMap: sin API key y sin cuota facturable. */}
      <TileLayer url={TILE_URL} attribution={TILE_ATTRIBUTION} maxZoom={19} />

      <FitBounds points={points} boundsKey={boundsKey} selected={selectedPoint} />

      {visibleRoutes.map((route) => {
        const placed = route.orders
          .filter(hasCoordinates)
          .slice()
          .sort((a, b) => (a.sequence ?? Number.MAX_SAFE_INTEGER) - (b.sequence ?? Number.MAX_SAFE_INTEGER));

        return (
          <Fragment key={route.id}>
            {showRouteLines && placed.length > 1 && (
              <Polyline
                positions={placed.map((order) => [order.lat, order.lng] as [number, number])}
                pathOptions={{ color: route.color, weight: 3, opacity: 0.55, dashArray: '6 8' }}
              />
            )}

            {placed.map((order, index) => (
              <Marker
                key={order.id}
                position={[order.lat, order.lng]}
                icon={routeIcon(
                  route.color,
                  String(order.sequence ?? index + 1),
                  order.status,
                  order.id === selectedOrderId,
                )}
                // Arrastrar el pin corrige una direccion mal geocodificada por
                // Nominatim sin salir del mapa.
                draggable={Boolean(onMoveOrder)}
                eventHandlers={{
                  click: () => onSelectOrder(order.id),
                  dragend: (event) => {
                    const { lat, lng } = (event.target as L.Marker).getLatLng();
                    onMoveOrder?.(order.id, lat, lng);
                  },
                }}
              >
                <Popup>
                  <OrderPopup order={order} routeCode={route.code} color={route.color} />
                </Popup>
              </Marker>
            ))}
          </Fragment>
        );
      })}

      {drivers
        .filter((driver) => driver.lastLat !== null && driver.lastLng !== null)
        .map((driver) => (
          <Marker
            key={driver.id}
            position={[driver.lastLat as number, driver.lastLng as number]}
            icon={driverIcon(driver.routeColor)}
            zIndexOffset={500}
          >
            <Popup>
              <div className="p-3">
                <p className="text-sm font-semibold text-content-primary">{driver.fullName}</p>
                <p className="text-xs text-content-secondary">
                  {driver.vehiclePlate ?? 'Sin placa'} ·{' '}
                  {driver.lastPingAt
                    ? `Reporte ${new Date(driver.lastPingAt).toLocaleTimeString('es-CO')}`
                    : 'Sin reportes'}
                </p>
              </div>
            </Popup>
          </Marker>
        ))}
    </MapContainer>
  );
}

function OrderPopup({
  order,
  routeCode,
  color,
}: {
  order: PlacedOrder;
  routeCode: string;
  color: string;
}) {
  const timeWindow = formatTimeWindow(order.timeWindowStart, order.timeWindowEnd);
  const status = ORDER_STATUS_META[order.status];
  const geocode = GEOCODE_STATUS_META[order.geocodeStatus];

  return (
    <div className="p-4">
      <div className="mb-2 flex items-center gap-2">
        <span
          className="rounded-full px-2 py-0.5 text-[11px] font-bold text-[#0b1017]"
          style={{ background: color }}
        >
          Ruta {routeCode}
        </span>
        <span className="text-[11px] font-medium" style={{ color: status.token }}>
          {status.label}
        </span>
      </div>

      <p className="text-sm font-semibold leading-tight text-content-primary">{order.clientNameRaw}</p>
      <p className="mt-0.5 font-mono text-[11px] text-content-muted">Doc. {order.documentNumber}</p>

      <p className="mt-2 text-xs leading-relaxed text-content-secondary">
        {order.address}
        {order.locality ? `, ${order.locality}` : ''}
      </p>

      <dl className="mt-3 grid grid-cols-3 gap-2 border-t border-border-subtle pt-3 text-center">
        <div>
          <dt className="text-[10px] uppercase tracking-wide text-content-muted">Peso</dt>
          <dd className="text-xs font-semibold text-content-primary">{formatKg(order.weightKg)}</dd>
        </div>
        <div>
          <dt className="text-[10px] uppercase tracking-wide text-content-muted">Unidades</dt>
          <dd className="text-xs font-semibold text-content-primary">{order.units}</dd>
        </div>
        <div>
          <dt className="text-[10px] uppercase tracking-wide text-content-muted">Items</dt>
          <dd className="text-xs font-semibold text-content-primary">{order.items}</dd>
        </div>
      </dl>

      {timeWindow && (
        <p className="mt-3 rounded-control bg-brand-soft px-2 py-1.5 text-[11px] font-medium text-brand">
          Ventana horaria: {timeWindow}
          {order.requiresAppointment ? ' · requiere cita' : ''}
        </p>
      )}

      {order.comments && (
        <p className="mt-2 text-[11px] leading-relaxed text-content-muted">{order.comments}</p>
      )}

      <p className="mt-2 text-[10px]" style={{ color: geocode.token }}>
        {geocode.label}
        {order.geocodeStatus !== 'MANUAL' && ' · arrastra el pin para corregir'}
      </p>
    </div>
  );
}
