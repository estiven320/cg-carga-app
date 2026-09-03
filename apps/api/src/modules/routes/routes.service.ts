import { Injectable, NotFoundException } from '@nestjs/common';
import { OrderStatus, RouteStatus } from '@prisma/client';
import { PrismaService } from '../../prisma/prisma.service';

export interface DashboardSummary {
  dispatchDate: string;
  routes: number;
  orders: number;
  delivered: number;
  failed: number;
  inTransit: number;
  pendingGeocode: number;
  totalWeightKg: number;
  totalUnits: number;
  completionRate: number;
}

const toDateOnly = (value?: string | Date): Date => {
  const date = value ? new Date(value) : new Date();
  return new Date(Date.UTC(date.getUTCFullYear(), date.getUTCMonth(), date.getUTCDate()));
};

@Injectable()
export class RoutesService {
  constructor(private readonly prisma: PrismaService) {}

  /** Rutas de la fecha con sus ordenes: es la carga inicial del dashboard. */
  async findByDate(date?: string) {
    const dispatchDate = toDateOnly(date);

    const routes = await this.prisma.route.findMany({
      where: { dispatchDate },
      orderBy: { code: 'asc' },
      include: {
        driver: { select: { id: true, fullName: true, phone: true, vehiclePlate: true, lastLat: true, lastLng: true, lastPingAt: true } },
        orders: {
          orderBy: [{ sequence: 'asc' }, { rowNumber: 'asc' }],
          select: {
            id: true,
            documentNumber: true,
            clientNameRaw: true,
            address: true,
            locality: true,
            lat: true,
            lng: true,
            geocodeStatus: true,
            geocodeLabel: true,
            weightKg: true,
            units: true,
            items: true,
            comments: true,
            timeWindowStart: true,
            timeWindowEnd: true,
            requiresAppointment: true,
            status: true,
            sequence: true,
            deliveredAt: true,
            _count: { select: { proofs: true } },
          },
        },
      },
    });

    return routes.map((route) => ({
      ...route,
      totalWeightKg: Number(route.totalWeightKg),
      orders: route.orders.map((order) => ({
        ...order,
        weightKg: Number(order.weightKg),
        proofCount: order._count.proofs,
        _count: undefined,
      })),
    }));
  }

  /**
   * GeoJSON FeatureCollection listo para Leaflet. Cada feature carga el color
   * de su ruta, de modo que el frontend no tiene que cruzar dos endpoints para
   * pintar los marcadores.
   */
  async findAsGeoJson(date?: string) {
    const routes = await this.findByDate(date);

    return {
      type: 'FeatureCollection' as const,
      features: routes.flatMap((route) =>
        route.orders
          .filter((order) => order.lat !== null && order.lng !== null)
          .map((order) => ({
            type: 'Feature' as const,
            id: order.id,
            geometry: { type: 'Point' as const, coordinates: [order.lng!, order.lat!] },
            properties: {
              orderId: order.id,
              routeId: route.id,
              routeCode: route.code,
              color: route.color,
              documentNumber: order.documentNumber,
              client: order.clientNameRaw,
              address: order.address,
              locality: order.locality,
              status: order.status,
              geocodeStatus: order.geocodeStatus,
              weightKg: order.weightKg,
              units: order.units,
              items: order.items,
              timeWindow:
                order.timeWindowStart || order.timeWindowEnd
                  ? `${order.timeWindowStart ?? ''}-${order.timeWindowEnd ?? ''}`
                  : null,
              comments: order.comments,
              sequence: order.sequence,
            },
          })),
      ),
    };
  }

  async summary(date?: string): Promise<DashboardSummary> {
    const dispatchDate = toDateOnly(date);
    const where = { route: { dispatchDate } };

    const [routes, orders, delivered, failed, inTransit, pendingGeocode, totals] = await Promise.all([
      this.prisma.route.count({ where: { dispatchDate } }),
      this.prisma.order.count({ where }),
      this.prisma.order.count({ where: { ...where, status: OrderStatus.DELIVERED } }),
      this.prisma.order.count({ where: { ...where, status: OrderStatus.FAILED } }),
      this.prisma.order.count({ where: { ...where, status: { in: [OrderStatus.IN_TRANSIT, OrderStatus.ARRIVED] } } }),
      this.prisma.order.count({ where: { ...where, geocodeStatus: { in: ['PENDING', 'NOT_FOUND', 'ERROR'] } } }),
      this.prisma.order.aggregate({ where, _sum: { weightKg: true, units: true } }),
    ]);

    return {
      dispatchDate: dispatchDate.toISOString().slice(0, 10),
      routes,
      orders,
      delivered,
      failed,
      inTransit,
      pendingGeocode,
      totalWeightKg: Number(totals._sum.weightKg ?? 0),
      totalUnits: totals._sum.units ?? 0,
      completionRate: orders > 0 ? delivered / orders : 0,
    };
  }

  async assignDriver(routeId: string, driverId: string) {
    const route = await this.prisma.route.findUnique({ where: { id: routeId } });
    if (!route) throw new NotFoundException(`Ruta ${routeId} no existe`);

    const [updated] = await this.prisma.$transaction([
      this.prisma.route.update({
        where: { id: routeId },
        data: { driverId, status: RouteStatus.ASSIGNED },
      }),
      this.prisma.order.updateMany({
        where: { routeId, status: OrderStatus.PENDING },
        data: { status: OrderStatus.ASSIGNED },
      }),
    ]);
    return updated;
  }

  /**
   * Secuencia las paradas por vecino mas cercano usando PostGIS (`<->`).
   * No pretende ser un VRP optimo: es una mejora barata sobre el orden del
   * Excel que reduce kilometros sin depender de un motor de ruteo pago.
   */
  async optimizeSequence(routeId: string, startLat: number, startLng: number) {
    const ordered = await this.prisma.$queryRaw<Array<{ id: string; seq: number }>>`
      WITH RECURSIVE nn AS (
        SELECT
          o.id,
          1 AS seq,
          o.geom AS current_geom,
          ARRAY[o.id] AS visited
        FROM orders o
        WHERE o.route_id = ${routeId}::uuid AND o.geom IS NOT NULL
        ORDER BY o.geom <-> ST_SetSRID(ST_MakePoint(${startLng}, ${startLat}), 4326)::geography
        LIMIT 1

        UNION ALL

        SELECT next.id, nn.seq + 1, next.geom, nn.visited || next.id
        FROM nn
        CROSS JOIN LATERAL (
          SELECT o.id, o.geom
          FROM orders o
          WHERE o.route_id = ${routeId}::uuid
            AND o.geom IS NOT NULL
            AND NOT (o.id = ANY(nn.visited))
          ORDER BY o.geom <-> nn.current_geom
          LIMIT 1
        ) AS next
      )
      SELECT id, seq FROM nn
    `;

    await this.prisma.$transaction(
      ordered.map((row) =>
        this.prisma.order.update({ where: { id: row.id }, data: { sequence: Number(row.seq) } }),
      ),
    );

    return { routeId, stops: ordered.length };
  }

  /** Ordenes dentro del viewport actual del mapa (PostGIS + indice GIST). */
  async findInBoundingBox(bbox: { south: number; west: number; north: number; east: number }, date?: string) {
    const dispatchDate = toDateOnly(date);
    return this.prisma.$queryRaw<
      Array<{ id: string; lat: number; lng: number; route_code: string; color: string; status: string }>
    >`
      SELECT o.id, o.lat, o.lng, r.code AS route_code, r.color, o.status::text
      FROM orders o
      JOIN routes r ON r.id = o.route_id
      WHERE r.dispatch_date = ${dispatchDate}
        AND o.geom && ST_MakeEnvelope(${bbox.west}, ${bbox.south}, ${bbox.east}, ${bbox.north}, 4326)::geography
      LIMIT 5000
    `;
  }
}
