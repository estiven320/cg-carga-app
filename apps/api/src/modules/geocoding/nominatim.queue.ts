import { Injectable, Logger } from '@nestjs/common';
import { ConfigService } from '@nestjs/config';
import type { NominatimConfig } from '../../config/configuration';

type QueuedTask<T> = {
  run: () => Promise<T>;
  resolve: (value: T) => void;
  reject: (reason: unknown) => void;
  label: string;
};

/**
 * Cola serializada con intervalo minimo garantizado entre peticiones.
 *
 * La politica de uso de Nominatim publico prohibe mas de 1 peticion por segundo
 * y bloquea por IP a quien la incumple. Como una importacion puede disparar
 * cientos de geocodificaciones concurrentes, TODAS pasan por aqui: la cola
 * ejecuta de a una tarea y espera `minIntervalMs` desde el inicio de la
 * anterior antes de lanzar la siguiente.
 *
 * Es un singleton de proceso. Si algun dia se escala a varias replicas del API,
 * el reemplazo natural es un rate limiter distribuido (token bucket en Redis)
 * o directamente un Nominatim self-hosted, que elimina el limite.
 */
@Injectable()
export class NominatimQueue {
  private readonly logger = new Logger(NominatimQueue.name);
  private readonly config: NominatimConfig;
  private readonly queue: QueuedTask<any>[] = [];
  private running = false;
  private lastStartedAt = 0;

  /** Metricas expuestas en GET /api/geocoding/health. */
  private stats = { enqueued: 0, executed: 0, failed: 0, throttledMs: 0 };

  constructor(configService: ConfigService) {
    this.config = configService.getOrThrow<NominatimConfig>('nominatim');
  }

  get pending(): number {
    return this.queue.length;
  }

  getStats() {
    return { ...this.stats, pending: this.queue.length, minIntervalMs: this.config.minIntervalMs };
  }

  /** Estimacion en ms de cuanto tardaria vaciar la cola. Se usa en la UI. */
  estimateDrainMs(extraTasks = 0): number {
    return (this.queue.length + extraTasks) * this.config.minIntervalMs;
  }

  enqueue<T>(label: string, run: () => Promise<T>): Promise<T> {
    this.stats.enqueued += 1;
    return new Promise<T>((resolve, reject) => {
      this.queue.push({ run, resolve, reject, label });
      void this.drain();
    });
  }

  private async drain(): Promise<void> {
    if (this.running) return;
    this.running = true;

    try {
      while (this.queue.length > 0) {
        const task = this.queue.shift()!;
        const waitMs = this.config.minIntervalMs - (Date.now() - this.lastStartedAt);

        if (waitMs > 0) {
          this.stats.throttledMs += waitMs;
          await sleep(waitMs);
        }

        this.lastStartedAt = Date.now();
        try {
          const result = await task.run();
          this.stats.executed += 1;
          task.resolve(result);
        } catch (error) {
          this.stats.failed += 1;
          this.logger.warn(`Tarea "${task.label}" fallo: ${(error as Error).message}`);
          task.reject(error);
        }
      }
    } finally {
      this.running = false;
    }
  }
}

export const sleep = (ms: number): Promise<void> =>
  new Promise((resolve) => setTimeout(resolve, ms));
