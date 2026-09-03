import { Injectable, Logger } from '@nestjs/common';
import { ConfigService } from '@nestjs/config';
import { GeocodeStatus, ImportStatus, Prisma, RouteStatus } from '@prisma/client';
import { PrismaService } from '../../prisma/prisma.service';
import { ProgressBus } from '../../common/events/progress.bus';
import { GeocodingService } from '../geocoding/geocoding.service';
import { NominatimQueue } from '../geocoding/nominatim.queue';
import { ExcelParserService, type ParsedOrderRow, type ParseIssue } from './excel-parser.service';
import { colorForRoute } from './route-color';

export interface ImportOptions {
  sheetName?: string;
  dispatchDate?: Date;
  userId?: string;
  /** Si es false, la geocodificacion queda pendiente para un job posterior. */
  geocode?: boolean;
}

@Injectable()
export class DispatchImportService {
  private readonly logger = new Logger(DispatchImportService.name);
  private readonly defaultSheet: string;

  constructor(
    private readonly prisma: PrismaService,
    private readonly parser: ExcelParserService,
    private readonly geocoding: GeocodingService,
    private readonly queue: NominatimQueue,
    private readonly progress: ProgressBus,
    configService: ConfigService,
  ) {
    this.defaultSheet = configService.get<string>('import.defaultSheet') ?? 'PROGRAMACION 3 DE SEPTIEMBRE';
  }

  /**
   * Punto de entrada del flujo de despacho.
   *
   * Es deliberadamente en dos fases:
   *   FASE 1 (sincrona, segundos): parsear y persistir. El despachador ve las
   *          rutas y las ordenes de inmediato, aunque sin coordenadas.
   *   FASE 2 (asincrona, minutos): geocodificar a 1 req/s. Cada orden resuelta
   *          se emite por WebSocket y aparece en el mapa en vivo.
   *
   * Hacerlo todo sincrono significaria dejar colgada la peticion HTTP ~3.5 min
   * para una programacion de 200 filas.
   */
  async importFile(
    file: { originalname: string; buffer: Buffer },
    options: ImportOptions = {},
  ) {
    const sheetName = options.sheetName ?? this.defaultSheet;
    const parsed = await this.parser.parse(file.buffer, sheetName, options.dispatchDate);

    const batch = await this.prisma.importBatch.create({
      data: {
        filename: file.originalname,
        sheetName: parsed.sheetName,
        dispatchDate: parsed.dispatchDate,
        status: ImportStatus.PROCESSING,
        totalRows: parsed.totalRows,
        skippedRows: parsed.skippedRows,
        errors: parsed.issues as unknown as Prisma.InputJsonValue,
        createdById: options.userId ?? null,
      },
    });

    const { imported, failed, issues } = await this.persistRows(batch.id, parsed.rows, parsed.dispatchDate);

    const allIssues = [...parsed.issues, ...issues];
    await this.prisma.importBatch.update({
      where: { id: batch.id },
      data: {
        importedRows: imported,
        failedRows: failed,
        errors: allIssues as unknown as Prisma.InputJsonValue,
        status: failed > 0 ? ImportStatus.COMPLETED_WITH_ERRORS : ImportStatus.COMPLETED,
        finishedAt: new Date(),
      },
    });

    await this.refreshRouteTotals(parsed.dispatchDate);

    const pendingGeocode = await this.prisma.order.count({
      where: { importBatchId: batch.id, geocodeStatus: GeocodeStatus.PENDING },
    });

    if (options.geocode !== false && pendingGeocode > 0) {
      // Fase 2 en segundo plano; los errores se registran, no tumban el request.
      void this.geocodeBatch(batch.id).catch((error) =>
        this.logger.error(`Geocodificacion del lote ${batch.id} fallo: ${(error as Error).message}`),
      );
    }

    return {
      batchId: batch.id,
      sheetName: parsed.sheetName,
      dispatchDate: parsed.dispatchDate,
      headerRowNumber: parsed.headerRowNumber,
      unmappedHeaders: parsed.unmappedHeaders,
      totalRows: parsed.totalRows,
      imported,
      skipped: parsed.skippedRows,
      failed,
      issues: allIssues.slice(0, 100),
      pendingGeocode,
      /** Estimacion honesta para la barra de progreso del dashboard. */
      estimatedGeocodeMs: this.queue.estimateDrainMs(pendingGeocode),
    };
  }

  // ------------------------------------------------------------ persistencia

  private async persistRows(batchId: string, rows: ParsedOrderRow[], dispatchDate: Date) {
    const issues: ParseIssue[] = [];
    let imported = 0;
    let failed = 0;

    // Cache local para no repetir upserts de la misma ruta/cliente por fila.
    const routeIds = new Map<string, string>();
    const clientIds = new Map<string, string>();

    for (const row of rows) {
      try {
        let routeId = routeIds.get(row.routeCode);
        if (!routeId) {
          const route = await this.prisma.route.upsert({
            where: { code_dispatchDate: { code: row.routeCode, dispatchDate } },
            create: {
              code: row.routeCode,
              dispatchDate,
              color: colorForRoute(row.routeCode),
              status: RouteStatus.DRAFT,
            },
            update: {},
          });
          routeId = route.id;
          routeIds.set(row.routeCode, routeId);
        }

        let clientId = clientIds.get(row.documentNumber);
        if (!clientId) {
          const client = await this.prisma.client.upsert({
            where: { documentNumber: row.documentNumber },
            create: {
              documentNumber: row.documentNumber,
              name: row.clientName,
              defaultAddress: row.address,
              defaultLocality: row.locality,
            },
            update: {
              name: row.clientName,
              defaultAddress: row.address,
              defaultLocality: row.locality,
            },
          });
          clientId = client.id;
          clientIds.set(row.documentNumber, clientId);
        }

        const payload = {
          clientId,
          documentNumber: row.documentNumber,
          clientNameRaw: row.clientName,
          address: row.address,
          locality: row.locality,
          weightKg: new Prisma.Decimal(row.weightKg),
          units: row.units,
          items: row.items,
          comments: row.comments,
          timeWindowStart: row.timeWindow.start,
          timeWindowEnd: row.timeWindow.end,
          requiresAppointment: row.timeWindow.requiresAppointment,
          rowNumber: row.rowNumber,
          importBatchId: batchId,
        };

        await this.prisma.order.upsert({
          where: { routeId_documentNumber: { routeId, documentNumber: row.documentNumber } },
          create: { routeId, ...payload },
          // Reimportar el mismo Excel corregido actualiza los datos pero
          // conserva estado operativo, coordenadas y evidencias ya cargadas.
          update: payload,
        });

        imported += 1;
      } catch (error) {
        failed += 1;
        issues.push({ row: row.rowNumber, message: (error as Error).message });
        this.logger.warn(`Fila ${row.rowNumber} fallo: ${(error as Error).message}`);
      }

      if (imported % 25 === 0) {
        this.progress.publish({
          type: 'import.progress',
          batchId,
          stage: 'persisting',
          done: imported,
          total: rows.length,
        });
      }
    }

    return { imported, failed, issues };
  }

  // ---------------------------------------------------------- geocodificacion

  /**
   * Fase 2: resuelve las direcciones del lote. El throttling de 1 req/s vive en
   * NominatimQueue, aqui solo se recorre y se emite progreso.
   */
  async geocodeBatch(batchId: string): Promise<{ resolved: number; failed: number }> {
    const orders = await this.prisma.order.findMany({
      where: { importBatchId: batchId, geocodeStatus: GeocodeStatus.PENDING },
      select: { id: true, routeId: true, address: true, locality: true },
      orderBy: { rowNumber: 'asc' },
    });

    let resolved = 0;
    let failed = 0;

    for (const [index, order] of orders.entries()) {
      const result = await this.geocoding.geocode(order.address, order.locality);

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

      if (result.lat !== null) resolved += 1;
      else failed += 1;

      this.progress.publish({
        type: 'import.progress',
        batchId,
        stage: 'geocoding',
        done: index + 1,
        total: orders.length,
        etaMs: this.queue.estimateDrainMs(),
      });
      this.progress.publish({
        type: 'order.updated',
        orderId: order.id,
        routeId: order.routeId,
        status: result.status,
        lat: result.lat,
        lng: result.lng,
      });
    }

    await this.prisma.importBatch.update({
      where: { id: batchId },
      data: { geocodeHits: resolved, geocodeFailures: failed },
    });
    this.progress.publish({ type: 'import.completed', batchId, imported: resolved, failed });

    return { resolved, failed };
  }

  /** Recalcula los totales denormalizados de cada ruta de la fecha. */
  async refreshRouteTotals(dispatchDate: Date): Promise<void> {
    const routes = await this.prisma.route.findMany({
      where: { dispatchDate },
      select: { id: true },
    });

    for (const route of routes) {
      const aggregate = await this.prisma.order.aggregate({
        where: { routeId: route.id },
        _count: { _all: true },
        _sum: { weightKg: true, units: true, items: true },
      });
      const delivered = await this.prisma.order.count({
        where: { routeId: route.id, status: 'DELIVERED' },
      });
      const failedCount = await this.prisma.order.count({
        where: { routeId: route.id, status: 'FAILED' },
      });

      await this.prisma.route.update({
        where: { id: route.id },
        data: {
          totalOrders: aggregate._count._all,
          totalWeightKg: aggregate._sum.weightKg ?? new Prisma.Decimal(0),
          totalUnits: aggregate._sum.units ?? 0,
          totalItems: aggregate._sum.items ?? 0,
          deliveredCount: delivered,
          failedCount,
        },
      });
    }
  }

  async getBatch(batchId: string) {
    return this.prisma.importBatch.findUnique({
      where: { id: batchId },
      include: { _count: { select: { orders: true } } },
    });
  }

  listSheets(buffer: Buffer): Promise<string[]> {
    return this.parser.listSheets(buffer);
  }
}
