import { Logger, type OnModuleInit } from '@nestjs/common';
import {
  ConnectedSocket,
  MessageBody,
  SubscribeMessage,
  WebSocketGateway,
  WebSocketServer,
} from '@nestjs/websockets';
import type { Server, Socket } from 'socket.io';
import { ProgressBus } from '../../common/events/progress.bus';
import { DriversService } from '../drivers/drivers.service';

/**
 * Canal en vivo del dashboard.
 *
 * Emite:
 *  - `import.progress`  barra de avance de la geocodificacion (1 req/s).
 *  - `order.updated`    cambio de estado o de coordenada de una entrega.
 *  - `driver.ping`      posicion GPS del conductor para mover su icono.
 *
 * Recibe de la app Flutter:
 *  - `driver.ping`      { driverId, routeId, lat, lng, recordedAt }
 *
 * Se usan salas por fecha de despacho para que un dashboard abierto en el dia
 * de ayer no reciba el trafico de hoy.
 */
@WebSocketGateway({ namespace: '/realtime', cors: { origin: true, credentials: true } })
export class RealtimeGateway implements OnModuleInit {
  private readonly logger = new Logger(RealtimeGateway.name);

  @WebSocketServer()
  server!: Server;

  constructor(
    private readonly progress: ProgressBus,
    private readonly drivers: DriversService,
  ) {}

  onModuleInit(): void {
    this.progress.asObservable().subscribe((event) => {
      this.server?.emit(event.type, event);
    });
  }

  @SubscribeMessage('subscribe')
  subscribe(@ConnectedSocket() client: Socket, @MessageBody() body: { dispatchDate?: string }) {
    const room = `dispatch:${body?.dispatchDate ?? 'today'}`;
    void client.join(room);
    return { ok: true, room };
  }

  @SubscribeMessage('driver.ping')
  async ping(
    @MessageBody()
    body: { driverId: string; routeId?: string; lat: number; lng: number; accuracyM?: number; speedKmh?: number; batteryPct?: number; recordedAt?: string },
  ) {
    await this.drivers.recordPing({
      driverId: body.driverId,
      routeId: body.routeId,
      lat: body.lat,
      lng: body.lng,
      accuracyM: body.accuracyM,
      speedKmh: body.speedKmh,
      batteryPct: body.batteryPct,
      recordedAt: body.recordedAt ? new Date(body.recordedAt) : new Date(),
    });
    return { ok: true };
  }
}
