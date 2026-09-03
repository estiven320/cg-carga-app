import { Injectable, Logger, OnModuleInit } from '@nestjs/common';
import { ConfigService } from '@nestjs/config';
import { Client as MinioClient } from 'minio';
import { randomUUID } from 'node:crypto';
import type { MinioConfig } from '../../config/configuration';

export interface PresignedUpload {
  uploadUrl: string;
  objectKey: string;
  bucket: string;
  expiresInSeconds: number;
}

/**
 * MinIO = S3 self-hosted. Reemplaza a AWS S3 / Cloud Storage sin costo de
 * licencia ni de egreso.
 *
 * Patron de subida elegido: URL prefirmada. La app Flutter sube la foto
 * DIRECTAMENTE a MinIO y luego confirma al API con la llave del objeto. Ventajas
 * frente a hacer proxy del binario por NestJS:
 *  - el API no consume RAM ni ancho de banda con archivos de varios MB,
 *  - la subida sobrevive a reinicios del API,
 *  - se puede reintentar desde la app sin volver a autenticar.
 */
@Injectable()
export class StorageService implements OnModuleInit {
  private readonly logger = new Logger(StorageService.name);
  private readonly config: MinioConfig;
  private readonly client: MinioClient;

  constructor(configService: ConfigService) {
    this.config = configService.getOrThrow<MinioConfig>('minio');
    this.client = new MinioClient({
      endPoint: this.config.endPoint,
      port: this.config.port,
      useSSL: this.config.useSSL,
      accessKey: this.config.accessKey,
      secretKey: this.config.secretKey,
      region: this.config.region,
    });
  }

  async onModuleInit(): Promise<void> {
    try {
      const exists = await this.client.bucketExists(this.config.bucket);
      if (!exists) {
        await this.client.makeBucket(this.config.bucket, this.config.region);
        this.logger.log(`Bucket "${this.config.bucket}" creado`);
      }
    } catch (error) {
      // No se tumba el arranque del API: el resto del TMS funciona sin POD.
      this.logger.error(`MinIO no disponible: ${(error as Error).message}`);
    }
  }

  /** Llave jerarquica por fecha: facilita politicas de retencion y backups. */
  buildObjectKey(orderId: string, extension = 'jpg'): string {
    const now = new Date();
    const yyyy = now.getUTCFullYear();
    const mm = String(now.getUTCMonth() + 1).padStart(2, '0');
    const dd = String(now.getUTCDate()).padStart(2, '0');
    return `${yyyy}/${mm}/${dd}/${orderId}/${randomUUID()}.${extension.replace(/^\./, '')}`;
  }

  async createPresignedUpload(orderId: string, extension = 'jpg'): Promise<PresignedUpload> {
    const objectKey = this.buildObjectKey(orderId, extension);
    const uploadUrl = await this.client.presignedPutObject(
      this.config.bucket,
      objectKey,
      this.config.presignExpirySeconds,
    );
    return {
      uploadUrl,
      objectKey,
      bucket: this.config.bucket,
      expiresInSeconds: this.config.presignExpirySeconds,
    };
  }

  /** URL temporal de lectura para mostrar la evidencia en el dashboard. */
  getDownloadUrl(objectKey: string, expirySeconds?: number): Promise<string> {
    return this.client.presignedGetObject(
      this.config.bucket,
      objectKey,
      expirySeconds ?? this.config.presignExpirySeconds,
    );
  }

  /** Ruta alternativa: subida por proxy, util cuando MinIO no es alcanzable
   *  desde la red movil y solo el API esta expuesto. */
  async putObject(objectKey: string, buffer: Buffer, mimeType: string): Promise<void> {
    await this.client.putObject(this.config.bucket, objectKey, buffer, buffer.length, {
      'Content-Type': mimeType,
    });
  }

  async statObject(objectKey: string) {
    return this.client.statObject(this.config.bucket, objectKey);
  }

  async removeObject(objectKey: string): Promise<void> {
    await this.client.removeObject(this.config.bucket, objectKey);
  }

  get bucket(): string {
    return this.config.bucket;
  }
}
