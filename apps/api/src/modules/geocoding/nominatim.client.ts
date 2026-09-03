import { Injectable, Logger } from '@nestjs/common';
import { ConfigService } from '@nestjs/config';
import { request } from 'undici';
import type { NominatimConfig } from '../../config/configuration';
import { NominatimQueue, sleep } from './nominatim.queue';

export interface NominatimPlace {
  place_id: number;
  osm_type?: string;
  osm_id?: number;
  lat: string;
  lon: string;
  display_name: string;
  class?: string;
  type?: string;
  place_rank?: number;
  importance?: number;
  boundingbox?: string[];
  address?: Record<string, string>;
}

export interface SearchOptions {
  /** Consulta libre ya normalizada (incluye ", COLOMBIA"). */
  query: string;
  limit?: number;
  /** Se antepone `countrycodes=co` para no traer resultados de otros paises. */
  countryCodes?: string;
}

/**
 * Cliente HTTP de Nominatim. No conoce el cache ni la base de datos: su unica
 * responsabilidad es hablar con la API respetando la politica de uso.
 *
 * Reglas que implementa (obligatorias segun la OSMF):
 *  - User-Agent identificable (una app sin UA propio recibe 403).
 *  - Maximo 1 req/s -> delegado en NominatimQueue.
 *  - Backoff exponencial ante 429 / 5xx, sin martillar el servicio.
 */
@Injectable()
export class NominatimClient {
  private readonly logger = new Logger(NominatimClient.name);
  private readonly config: NominatimConfig;

  constructor(
    configService: ConfigService,
    private readonly queue: NominatimQueue,
  ) {
    this.config = configService.getOrThrow<NominatimConfig>('nominatim');
  }

  /**
   * Encola una busqueda. La promesa se resuelve cuando la cola concede turno,
   * por lo que el llamador puede usar `await` sin preocuparse por el rate limit.
   */
  async search(options: SearchOptions): Promise<NominatimPlace[]> {
    return this.queue.enqueue(options.query, () => this.executeWithRetry(options));
  }

  /** Geocodificacion inversa: usada al recibir el GPS del conductor. */
  async reverse(lat: number, lon: number): Promise<NominatimPlace | null> {
    return this.queue.enqueue(`reverse:${lat},${lon}`, async () => {
      const url = this.buildUrl('/reverse', {
        lat: String(lat),
        lon: String(lon),
        format: 'jsonv2',
        addressdetails: '1',
      });
      const place = await this.fetchJson<NominatimPlace>(url);
      return place && (place as any).lat ? place : null;
    });
  }

  private async executeWithRetry(options: SearchOptions): Promise<NominatimPlace[]> {
    const url = this.buildUrl('/search', {
      q: options.query,
      format: 'jsonv2',
      addressdetails: '1',
      limit: String(options.limit ?? 1),
      countrycodes: options.countryCodes ?? this.config.countryCodes,
    });

    let lastError: unknown;
    for (let attempt = 1; attempt <= this.config.maxRetries; attempt += 1) {
      try {
        return (await this.fetchJson<NominatimPlace[]>(url)) ?? [];
      } catch (error) {
        lastError = error;
        const retryable = error instanceof RetryableNominatimError;
        if (!retryable || attempt === this.config.maxRetries) break;

        // 2s, 4s, 8s... el propio delay de la cola ya suma otro segundo.
        const backoffMs = 2 ** attempt * 1000;
        this.logger.warn(
          `Nominatim intento ${attempt}/${this.config.maxRetries} fallo (${(error as Error).message}). ` +
            `Reintentando en ${backoffMs} ms.`,
        );
        await sleep(backoffMs);
      }
    }
    throw lastError;
  }

  private buildUrl(path: string, params: Record<string, string>): string {
    const url = new URL(`${this.config.baseUrl}${path}`);
    for (const [key, value] of Object.entries(params)) {
      if (value) url.searchParams.set(key, value);
    }
    // Parametro de cortesia recomendado por la OSMF para poder contactarnos
    // antes de bloquear la IP si algo se sale de control.
    if (this.config.email) url.searchParams.set('email', this.config.email);
    return url.toString();
  }

  private async fetchJson<T>(url: string): Promise<T | null> {
    const response = await request(url, {
      method: 'GET',
      headers: {
        'User-Agent': this.config.userAgent,
        'Accept-Language': 'es',
        Accept: 'application/json',
      },
      headersTimeout: this.config.timeoutMs,
      bodyTimeout: this.config.timeoutMs,
    });

    const { statusCode } = response;

    if (statusCode === 429 || statusCode === 503 || statusCode >= 500) {
      response.body.dump();
      throw new RetryableNominatimError(`HTTP ${statusCode} desde Nominatim`);
    }
    if (statusCode >= 400) {
      const text = await response.body.text();
      throw new Error(`Nominatim respondio ${statusCode}: ${text.slice(0, 200)}`);
    }

    return (await response.body.json()) as T;
  }
}

export class RetryableNominatimError extends Error {}
