import { Injectable, NotFoundException } from '@nestjs/common';
import { EventType, OrderStatus, Prisma } from '@prisma/client';
import { PrismaService } from '../../prisma/prisma.service';
import { ProgressBus } from '../../common/events/progress.bus';

export interface UpdateStatusInput {
  status: OrderStatus;
  lat?: number;
  lng?: number;
  note?: string;
  failureReason?: string;
  receivedBy?: string;
  receivedByDocument?: string;
  userId?: string;
}

@Injectable()
export class OrdersService {
  constructor(
    private readonly prisma: PrismaService,
    private readonly progress: ProgressBus,
  ) {}

  async findOne(id: string) {
    const order = await this.prisma.order.findUnique({
      where: { id },
      include: {
        route: { select: { id: true, code: true, color: true, dispatchDate: true, driver: true } },
        client: true,
        proofs: { orderBy: { capturedAt: 'desc' } },
        events: { orderBy: { createdAt: 'desc' }, take: 50 },
      },
    });
    if (!order) throw new NotFoundException(`Orden ${id} no existe`);
    return { ...order, weightKg: Number(order.weightKg) };
  }

  /** Transicion de estado disparada por la app del conductor o el despachador. */
  async updateStatus(id: string, input: UpdateStatusInput) {
    const isFinal = input.status === OrderStatus.DELIVERED;

    const order = await this.prisma.order.update({
      where: { id },
      data: {
        status: input.status,
        deliveredAt: isFinal ? new Date() : undefined,
        failureReason: input.failureReason ?? null,
        receivedBy: input.receivedBy ?? undefined,
        receivedByDocument: input.receivedByDocument ?? undefined,
        // El GPS del conductor es la coordenada mas confiable que existe: si la
        // direccion venia mal geocodificada, la entrega la corrige.
        ...(input.lat !== undefined && input.lng !== undefined
          ? { lat: input.lat, lng: input.lng, geocodeSource: 'DRIVER_GPS' as const }
          : {}),
      },
    });

    await this.prisma.orderEvent.create({
      data: {
        orderId: id,
        userId: input.userId ?? null,
        type: this.eventTypeFor(input.status),
        message: input.note ?? input.failureReason ?? null,
        lat: input.lat ?? null,
        lng: input.lng ?? null,
        payload: { status: input.status } as Prisma.InputJsonValue,
      },
    });

    await this.refreshRouteCounters(order.routeId);

    this.progress.publish({
      type: 'order.updated',
      orderId: order.id,
      routeId: order.routeId,
      status: order.status,
      lat: order.lat,
      lng: order.lng,
    });

    return { ...order, weightKg: Number(order.weightKg) };
  }

  async reorder(routeId: string, orderedIds: string[]) {
    await this.prisma.$transaction(
      orderedIds.map((orderId, index) =>
        this.prisma.order.update({ where: { id: orderId }, data: { sequence: index + 1 } }),
      ),
    );
    return { routeId, stops: orderedIds.length };
  }

  private eventTypeFor(status: OrderStatus): EventType {
    switch (status) {
      case OrderStatus.DELIVERED:
        return EventType.DELIVERED;
      case OrderStatus.FAILED:
        return EventType.FAILED;
      case OrderStatus.RESCHEDULED:
        return EventType.RESCHEDULED;
      case OrderStatus.ARRIVED:
        return EventType.ARRIVED;
      case OrderStatus.IN_TRANSIT:
        return EventType.ROUTE_STARTED;
      default:
        return EventType.COMMENT;
    }
  }

  private async refreshRouteCounters(routeId: string): Promise<void> {
    const [delivered, failed, total] = await Promise.all([
      this.prisma.order.count({ where: { routeId, status: OrderStatus.DELIVERED } }),
      this.prisma.order.count({ where: { routeId, status: OrderStatus.FAILED } }),
      this.prisma.order.count({ where: { routeId } }),
    ]);

    await this.prisma.route.update({
      where: { id: routeId },
      data: {
        deliveredCount: delivered,
        failedCount: failed,
        ...(total > 0 && delivered + failed === total
          ? { status: 'COMPLETED' as const, completedAt: new Date() }
          : {}),
      },
    });
  }
}
