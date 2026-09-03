import { BadRequestException, Injectable, NotFoundException } from '@nestjs/common';
import { ProofType } from '@prisma/client';
import { createHash } from 'node:crypto';
import { PrismaService } from '../../prisma/prisma.service';
import { StorageService } from '../storage/storage.service';

export interface ConfirmProofInput {
  orderId: string;
  driverId?: string;
  objectKey: string;
  mimeType: string;
  sizeBytes: number;
  checksum?: string;
  type?: ProofType;
  lat?: number;
  lng?: number;
  note?: string;
  capturedAt: Date;
}

@Injectable()
export class ProofsService {
  constructor(
    private readonly prisma: PrismaService,
    private readonly storage: StorageService,
  ) {}

  /** Paso 1 del POD: la app pide una URL prefirmada antes de subir la foto. */
  async requestUpload(orderId: string, extension = 'jpg') {
    const order = await this.prisma.order.findUnique({ where: { id: orderId }, select: { id: true } });
    if (!order) throw new NotFoundException(`Orden ${orderId} no existe`);
    return this.storage.createPresignedUpload(orderId, extension);
  }

  /**
   * Paso 2: la app confirma la subida. Se verifica contra MinIO que el objeto
   * exista realmente antes de registrarlo, para que no queden evidencias
   * fantasma si la subida se corto a mitad de camino.
   */
  async confirmUpload(input: ConfirmProofInput) {
    const stat = await this.storage.statObject(input.objectKey).catch(() => null);
    if (!stat) {
      throw new BadRequestException(
        `El objeto "${input.objectKey}" no existe en MinIO. Reintente la subida.`,
      );
    }

    const distance = await this.distanceToOrder(input.orderId, input.lat, input.lng);

    return this.prisma.deliveryProof.upsert({
      // `checksum` da idempotencia: la app movil trabaja offline y reintenta.
      where: { orderId_checksum: { orderId: input.orderId, checksum: input.checksum ?? input.objectKey } },
      create: {
        orderId: input.orderId,
        driverId: input.driverId ?? null,
        type: input.type ?? ProofType.PHOTO,
        bucket: this.storage.bucket,
        objectKey: input.objectKey,
        mimeType: input.mimeType,
        sizeBytes: input.sizeBytes || Number(stat.size),
        checksum: input.checksum ?? input.objectKey,
        lat: input.lat ?? null,
        lng: input.lng ?? null,
        distanceToTargetM: distance,
        note: input.note ?? null,
        capturedAt: input.capturedAt,
      },
      update: { note: input.note ?? undefined },
    });
  }

  /** Ruta alternativa (proxy): la app envia el binario al API. */
  async uploadDirect(
    orderId: string,
    file: { buffer: Buffer; mimetype: string; originalname: string },
    meta: Omit<ConfirmProofInput, 'orderId' | 'objectKey' | 'mimeType' | 'sizeBytes' | 'checksum'>,
  ) {
    const extension = file.originalname.split('.').pop() ?? 'jpg';
    const objectKey = this.storage.buildObjectKey(orderId, extension);
    const checksum = createHash('sha256').update(file.buffer).digest('hex');

    await this.storage.putObject(objectKey, file.buffer, file.mimetype);

    return this.confirmUpload({
      ...meta,
      orderId,
      objectKey,
      mimeType: file.mimetype,
      sizeBytes: file.buffer.length,
      checksum,
    });
  }

  async listByOrder(orderId: string) {
    const proofs = await this.prisma.deliveryProof.findMany({
      where: { orderId },
      orderBy: { capturedAt: 'desc' },
    });

    return Promise.all(
      proofs.map(async (proof) => ({
        ...proof,
        url: await this.storage.getDownloadUrl(proof.objectKey),
      })),
    );
  }

  /**
   * Distancia entre la foto y la direccion geocodificada. Una evidencia tomada
   * a 3 km del destino es la senal mas util para auditar entregas dudosas.
   */
  private async distanceToOrder(orderId: string, lat?: number, lng?: number): Promise<number | null> {
    if (lat === undefined || lng === undefined) return null;

    const rows = await this.prisma.$queryRaw<Array<{ distance: number | null }>>`
      SELECT ST_Distance(
               o.geom,
               ST_SetSRID(ST_MakePoint(${lng}, ${lat}), 4326)::geography
             ) AS distance
      FROM orders o
      WHERE o.id = ${orderId}::uuid AND o.geom IS NOT NULL
    `;
    return rows[0]?.distance ?? null;
  }
}
