import { Injectable, Logger } from '@nestjs/common';
import { ConfigService } from '@nestjs/config';
import { GeocodeSource, GeocodeStatus, Prisma } from '@prisma/client';
import { PrismaService } from '../../prisma/prisma.service';
import type { NominatimConfig } from '../../config/configuration';
import { NominatimClient } from './nominatim.client';
import { NominatimQueue } from './nominatim.queue';
import {
  LOW_CONFIDENCE_THRESHOLD,
  normalizeAddress,
  scoreResult,
} from './address-normalizer';

export interface GeocodeResult {
  lat: number | null;
  lng: number | null;
  status: GeocodeStatus;
  source: GeocodeSource;
  score: number | null;
  label: string | null;
  normalizedQuery: string;
  /** true si se resolvio sin salir a la red. */
  cached: boolean;
}

/**
 * Servicio de geocodificacion con cache persistente.
 *
 * Estrategia de costo $0:
 *  1. Normalizar -> hash determinista.
 *  2. Buscar en `geocode_cache`. HIT vigente = 0 peticiones, 0 ms de espera.
 *  3. MISS -> NominatimClient (serializado a 1 req/s por NominatimQueue).
 *  4. Persistir SIEMPRE, incluidos NOT_FOUND, para no repetir consultas
 *     condenadas al fracaso en cada reimportacion del Excel.
 *
 * En una programacion tipica (~200 filas) la segunda corrida del mismo dia
 * resuelve el 100% desde cache: 0 peticiones externas y respuesta inmediata.
 */
@Injectable()
export class GeocodingService {
  private readonly logger = new Logger(GeocodingService.name);
  private readonly config: NominatimConfig;

  /**
   * Deduplicacion en vuelo: si 30 filas del Excel comparten la misma direccion
   * (muy comun con cadenas de tiendas), solo la primera sale a la red y las
   * otras 29 esperan esa misma promesa.
   */
  private readonly inFlight = new Map<string, Promise<GeocodeResult>>();

  constructor(
    private readonly prisma: PrismaService,
    private readonly nominatim: NominatimClient,
    private readonly queue: NominatimQueue,
    configService: ConfigService,
  ) {
    this.config = configService.getOrThrow<NominatimConfig>('nominatim');
  }

  async geocode(address: string, locality?: string | null): Promise<GeocodeResult> {
    const normalized = normalizeAddress(address, locality, this.config.countrySuffix);

    if (!normalized.street) {
      return {
        lat: null,
        lng: null,
        status: GeocodeStatus.NOT_FOUND,
        source: GeocodeSource.NOMINATIM,
        score: null,
        label: null,
        normalizedQuery: normalized.query,
        cached: false,
      };
    }

    const cached = await this.readCache(normalized.hash);
    if (cached) return cached;

    const existing = this.inFlight.get(normalized.hash);
    if (existing) return existing;

    const promise = this.resolveRemote(address, normalized).finally(() => {
      this.inFlight.delete(normalized.hash);
    });
    this.inFlight.set(normalized.hash, promise);
    return promise;
  }

  /** Geocodifica un lote respetando el rate limit; devuelve resultados en orden. */
  async geocodeBatch(
    entries: Array<{ address: string; locality?: string | null }>,
    onProgress?: (done: number, total: number) => void,
  ): Promise<GeocodeResult[]> {
    const results: GeocodeResult[] = [];
    for (const [index, entry] of entries.entries()) {
      results.push(await this.geocode(entry.address, entry.locality));
      onProgress?.(index + 1, entries.length);
    }
    return results;
  }

  // ------------------------------------------------------------------ cache

  private async readCache(queryHash: string): Promise<GeocodeResult | null> {
    const row = await this.prisma.geocodeCache.findUnique({ where: { queryHash } });
    if (!row) return null;

    // Entrada expirada: se ignora y se vuelve a consultar (las direcciones
    // cambian y OSM mejora con el tiempo).
    if (row.expiresAt && row.expiresAt.getTime() < Date.now()) return null;

    await this.prisma.geocodeCache.update({
      where: { id: row.id },
      data: { hitCount: { increment: 1 }, lastHitAt: new Date() },
    });

    return {
      lat: row.lat,
      lng: row.lng,
      status: row.status,
      source: GeocodeSource.CACHE,
      score: row.importance,
      label: row.displayName,
      normalizedQuery: row.normalizedQuery,
      cached: true,
    };
  }

  private async resolveRemote(
    rawAddress: string,
    normalized: ReturnType<typeof normalizeAddress>,
  ): Promise<GeocodeResult> {
    let places: Awaited<ReturnType<NominatimClient['search']>> = [];
    let status: GeocodeStatus;
    let errorMessage: string | null = null;

    try {
      places = await this.nominatim.search({ query: normalized.query, limit: 1 });
      status = places.length > 0 ? GeocodeStatus.RESOLVED : GeocodeStatus.NOT_FOUND;
    } catch (error) {
      status = GeocodeStatus.ERROR;
      errorMessage = (error as Error).message;
      this.logger.error(`Geocodificacion fallida para "${normalized.query}": ${errorMessage}`);
    }

    const place = places[0];
    const score = place ? scoreResult(place.place_rank, place.importance, place.class) : null;

    if (place && score !== null && score < LOW_CONFIDENCE_THRESHOLD) {
      status = GeocodeStatus.LOW_CONFIDENCE;
    }

    const lat = place ? Number.parseFloat(place.lat) : null;
    const lng = place ? Number.parseFloat(place.lon) : null;

    await this.writeCache({
      normalized,
      rawAddress,
      lat,
      lng,
      status,
      place,
      score,
      errorMessage,
    });

    return {
      lat,
      lng,
      status,
      source: GeocodeSource.NOMINATIM,
      score,
      label: place?.display_name ?? null,
      normalizedQuery: normalized.query,
      cached: false,
    };
  }

  private async writeCache(input: {
    normalized: ReturnType<typeof normalizeAddress>;
    rawAddress: string;
    lat: number | null;
    lng: number | null;
    status: GeocodeStatus;
    place?: { osm_type?: string; osm_id?: number; class?: string; place_rank?: number; importance?: number; display_name?: string; boundingbox?: string[] };
    score: number | null;
    errorMessage: string | null;
  }): Promise<void> {
    // Un fallo de red no debe envenenar el cache por 180 dias: TTL corto para
    // ERROR, medio para NOT_FOUND, completo para aciertos.
    const ttlDays =
      input.status === GeocodeStatus.ERROR ? 0.02 : // ~30 min
      input.status === GeocodeStatus.NOT_FOUND ? 7 :
      this.config.cacheTtlDays;

    const data = {
      rawQuery: input.rawAddress,
      normalizedQuery: input.normalized.query,
      locality: input.normalized.locality ?? null,
      countryCode: this.config.countryCodes.split(',')[0] ?? 'co',
      lat: input.lat,
      lng: input.lng,
      displayName: input.place?.display_name ?? null,
      osmType: input.place?.osm_type ?? null,
      osmId: input.place?.osm_id ? BigInt(input.place.osm_id) : null,
      osmClass: input.place?.class ?? null,
      placeRank: input.place?.place_rank ?? null,
      importance: input.score,
      boundingBox: (input.place?.boundingbox ?? Prisma.JsonNull) as Prisma.InputJsonValue,
      raw: input.errorMessage ? ({ error: input.errorMessage } as Prisma.InputJsonValue) : Prisma.JsonNull,
      status: input.status,
      lastHitAt: new Date(),
      expiresAt: new Date(Date.now() + ttlDays * 24 * 60 * 60 * 1000),
    };

    await this.prisma.geocodeCache.upsert({
      where: { queryHash: input.normalized.hash },
      create: { queryHash: input.normalized.hash, hitCount: 0, ...data },
      update: data,
    });
  }

  // ------------------------------------------------------------- correccion

  /** Correccion manual desde el dashboard (arrastrar el pin en el mapa). */
  async setManualCoordinates(orderId: string, lat: number, lng: number): Promise<void> {
    await this.prisma.order.update({
      where: { id: orderId },
      data: {
        lat,
        lng,
        geocodeStatus: GeocodeStatus.MANUAL,
        geocodeSource: GeocodeSource.MANUAL,
        geocodeScore: 1,
        geocodedAt: new Date(),
      },
    });
  }

  /** Reintenta las ordenes que quedaron sin coordenada utilizable. */
  async retryFailedOrders(dispatchDate?: Date): Promise<{ retried: number; resolved: number }> {
    const orders = await this.prisma.order.findMany({
      where: {
        geocodeStatus: { in: [GeocodeStatus.ERROR, GeocodeStatus.NOT_FOUND, GeocodeStatus.PENDING] },
        ...(dispatchDate ? { route: { dispatchDate } } : {}),
      },
      select: { id: true, address: true, locality: true },
      take: 500,
    });

    let resolved = 0;
    for (const order of orders) {
      const result = await this.geocode(order.address, order.locality);
      if (result.lat !== null && result.lng !== null) resolved += 1;
      await this.prisma.order.update({
        where: { id: order.id },
        data: {
          lat: result.lat,
          lng: result.lng,
          addressNormalized: result.normalizedQuery,
          geocodeStatus: result.status,
          geocodeSource: result.source,
          geocodeScore: result.score,
          geocodeLabel: result.label,
          geocodedAt: new Date(),
        },
      });
    }
    return { retried: orders.length, resolved };
  }

  async health() {
    const [total, resolved, pending] = await Promise.all([
      this.prisma.geocodeCache.count(),
      this.prisma.geocodeCache.count({ where: { status: GeocodeStatus.RESOLVED } }),
      this.prisma.order.count({ where: { geocodeStatus: GeocodeStatus.PENDING } }),
    ]);
    return {
      cache: { total, resolved, hitRatioHint: total > 0 ? resolved / total : 0 },
      ordersPendingGeocode: pending,
      queue: this.queue.getStats(),
    };
  }
}
