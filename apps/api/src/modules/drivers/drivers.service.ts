import { Injectable } from '@nestjs/common';
import { PrismaService } from '../../prisma/prisma.service';
import { ProgressBus } from '../../common/events/progress.bus';

export interface PingInput {
  driverId: string;
  routeId?: string | null;
  lat: number;
  lng: number;
  accuracyM?: number;
  speedKmh?: number;
  heading?: number;
  batteryPct?: number;
  recordedAt: Date;
}

@Injectable()
export class DriversService {
  constructor(
    private readonly prisma: PrismaService,
    private readonly progress: ProgressBus,
  ) {}

  findAll(activeOnly = true) {
    return this.prisma.driver.findMany({
      where: activeOnly ? { active: true } : {},
      orderBy: { fullName: 'asc' },
    });
  }

  /**
   * Guarda el rastro GPS y actualiza la ultima posicion del conductor.
   *
   * La app movil envia lotes cuando recupera senal, por eso se escribe el ping
   * historico siempre, pero `drivers.last_*` solo si el punto es mas reciente
   * que el ya almacenado: evita que un lote atrasado retroceda el icono.
   */
  async recordPing(input: PingInput) {
    const ping = await this.prisma.driverPing.create({
      data: {
        driverId: input.driverId,
        routeId: input.routeId ?? null,
        lat: input.lat,
        lng: input.lng,
        accuracyM: input.accuracyM ?? null,
        speedKmh: input.speedKmh ?? null,
        heading: input.heading ?? null,
        batteryPct: input.batteryPct ?? null,
        recordedAt: input.recordedAt,
      },
    });

    await this.prisma.driver.updateMany({
      where: {
        id: input.driverId,
        OR: [{ lastPingAt: null }, { lastPingAt: { lt: input.recordedAt } }],
      },
      data: { lastLat: input.lat, lastLng: input.lng, lastPingAt: input.recordedAt },
    });

    this.progress.publish({
      type: 'driver.ping',
      driverId: input.driverId,
      routeId: input.routeId ?? null,
      lat: input.lat,
      lng: input.lng,
      recordedAt: input.recordedAt.toISOString(),
    });

    return { id: Number(ping.id) };
  }

  /** Recorrido del dia para dibujar la polilinea real del conductor. */
  async track(driverId: string, from: Date, to: Date) {
    const pings = await this.prisma.driverPing.findMany({
      where: { driverId, recordedAt: { gte: from, lte: to } },
      orderBy: { recordedAt: 'asc' },
      select: { lat: true, lng: true, recordedAt: true, speedKmh: true },
    });
    return pings;
  }
}
