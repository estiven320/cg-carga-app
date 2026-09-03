import { Inject, Injectable, Logger, NotFoundException } from '@nestjs/common';
import { NotificationStatus } from '@prisma/client';
import { PrismaService } from '../../prisma/prisma.service';
import type { WhatsappProvider } from './whatsapp.provider';
import { WHATSAPP_PROVIDER } from './whatsapp.token';

@Injectable()
export class NotificationsService {
  private readonly logger = new Logger(NotificationsService.name);

  constructor(
    private readonly prisma: PrismaService,
    @Inject(WHATSAPP_PROVIDER) private readonly whatsapp: WhatsappProvider,
  ) {}

  /**
   * Envia al conductor el resumen de su ruta por WhatsApp.
   *
   * El mensaje se compone con los datos que el conductor realmente necesita en
   * la calle: orden de paradas, ventana horaria (extraida de COMENTARIOS) y
   * peso total, mas el enlace a la app movil.
   */
  async sendRouteToDriver(routeId: string, appUrl?: string) {
    const route = await this.prisma.route.findUnique({
      where: { id: routeId },
      include: {
        driver: true,
        orders: {
          orderBy: [{ sequence: 'asc' }, { rowNumber: 'asc' }],
          select: {
            documentNumber: true,
            clientNameRaw: true,
            address: true,
            locality: true,
            timeWindowStart: true,
            timeWindowEnd: true,
            requiresAppointment: true,
            weightKg: true,
          },
        },
      },
    });

    if (!route) throw new NotFoundException(`Ruta ${routeId} no existe`);
    if (!route.driver) throw new NotFoundException(`La ruta ${route.code} no tiene conductor asignado`);

    const body = this.buildRouteMessage(route, appUrl);
    return this.enqueueAndSend(route.driver.phone, body, routeId, 'route_assignment');
  }

  /** Alerta operativa: ordenes sin geocodificar, retrasos, novedades. */
  async sendAlert(phone: string, message: string, routeId?: string) {
    return this.enqueueAndSend(phone, message, routeId, 'alert');
  }

  async status() {
    return {
      provider: this.whatsapp.name,
      ready: await this.whatsapp.isReady(),
      queued: await this.prisma.notification.count({ where: { status: NotificationStatus.QUEUED } }),
      failed: await this.prisma.notification.count({ where: { status: NotificationStatus.FAILED } }),
    };
  }

  /** Reintenta lo que quedo en cola (ej. tras reconectar WhatsApp Web). */
  async retryQueued(limit = 50) {
    const pending = await this.prisma.notification.findMany({
      where: { status: { in: [NotificationStatus.QUEUED, NotificationStatus.FAILED] }, attempts: { lt: 5 } },
      take: limit,
      orderBy: { createdAt: 'asc' },
    });

    let sent = 0;
    for (const notification of pending) {
      const result = await this.whatsapp.send(notification.recipient, notification.body);
      await this.prisma.notification.update({
        where: { id: notification.id },
        data: {
          status: result.ok ? NotificationStatus.SENT : NotificationStatus.FAILED,
          providerMessageId: result.providerMessageId ?? null,
          error: result.error ?? null,
          attempts: { increment: 1 },
          sentAt: result.ok ? new Date() : null,
        },
      });
      if (result.ok) sent += 1;
    }
    return { attempted: pending.length, sent };
  }

  private async enqueueAndSend(recipient: string, body: string, routeId?: string, template?: string) {
    // Se persiste ANTES de enviar: si el proveedor esta caido, el mensaje queda
    // en cola y `retryQueued` lo recupera; nunca se pierde una asignacion.
    const notification = await this.prisma.notification.create({
      data: { routeId: routeId ?? null, recipient, body, template: template ?? null },
    });

    const result = await this.whatsapp.send(recipient, body);

    return this.prisma.notification.update({
      where: { id: notification.id },
      data: {
        status: result.ok ? NotificationStatus.SENT : NotificationStatus.FAILED,
        providerMessageId: result.providerMessageId ?? null,
        error: result.error ?? null,
        attempts: 1,
        sentAt: result.ok ? new Date() : null,
      },
    });
  }

  private buildRouteMessage(
    route: { code: string; dispatchDate: Date; totalWeightKg: unknown; orders: any[]; driver: { fullName: string } | null },
    appUrl?: string,
  ): string {
    const date = route.dispatchDate.toISOString().slice(0, 10);
    const lines = [
      `*CG CARGA - Ruta ${route.code}*`,
      `Fecha: ${date}`,
      `Conductor: ${route.driver?.fullName ?? '-'}`,
      `Paradas: ${route.orders.length} | Peso total: ${Number(route.totalWeightKg).toFixed(1)} kg`,
      '',
    ];

    route.orders.forEach((order, index) => {
      const window =
        order.timeWindowStart || order.timeWindowEnd
          ? ` (${order.timeWindowStart ?? '--:--'} a ${order.timeWindowEnd ?? '--:--'})`
          : '';
      const appointment = order.requiresAppointment ? ' [CITA]' : '';
      lines.push(
        `${index + 1}. ${order.clientNameRaw}${appointment}`,
        `   ${order.address}${order.locality ? `, ${order.locality}` : ''}${window}`,
        `   Doc: ${order.documentNumber} | ${Number(order.weightKg).toFixed(1)} kg`,
      );
    });

    if (appUrl) {
      lines.push('', `Abrir en la app: ${appUrl}`);
    }
    return lines.join('\n');
  }
}
