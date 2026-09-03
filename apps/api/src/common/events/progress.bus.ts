import { Global, Injectable, Module } from '@nestjs/common';
import { Subject, type Observable } from 'rxjs';

export type ProgressEvent =
  | { type: 'import.progress'; batchId: string; stage: 'parsing' | 'persisting' | 'geocoding'; done: number; total: number; etaMs?: number }
  | { type: 'import.completed'; batchId: string; imported: number; failed: number }
  | { type: 'order.updated'; orderId: string; routeId: string; status: string; lat?: number | null; lng?: number | null }
  | { type: 'driver.ping'; driverId: string; routeId?: string | null; lat: number; lng: number; recordedAt: string };

/**
 * Bus interno en memoria. Desacopla los servicios de dominio del gateway de
 * WebSocket: `ImportService` publica progreso sin conocer socket.io, y
 * `RealtimeGateway` reemite a los clientes conectados.
 */
@Injectable()
export class ProgressBus {
  private readonly subject = new Subject<ProgressEvent>();

  publish(event: ProgressEvent): void {
    this.subject.next(event);
  }

  asObservable(): Observable<ProgressEvent> {
    return this.subject.asObservable();
  }
}

@Global()
@Module({ providers: [ProgressBus], exports: [ProgressBus] })
export class ProgressBusModule {}
