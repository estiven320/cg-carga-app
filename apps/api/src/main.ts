import 'reflect-metadata';
import { Logger, ValidationPipe } from '@nestjs/common';
import { ConfigService } from '@nestjs/config';
import { NestFactory } from '@nestjs/core';
import { DocumentBuilder, SwaggerModule } from '@nestjs/swagger';
import { json } from 'express';
import { AppModule } from './app.module';

/**
 * Prisma serializa `BigInt` (osm_id, ids de pings) y JSON.stringify no sabe
 * manejarlo. Se define el serializador una sola vez, en el arranque.
 */
(BigInt.prototype as unknown as { toJSON: () => string }).toJSON = function toJSON() {
  return this.toString();
};

async function bootstrap(): Promise<void> {
  const app = await NestFactory.create(AppModule, { bufferLogs: true });
  const config = app.get(ConfigService);

  app.setGlobalPrefix('api');
  app.use(json({ limit: '5mb' }));
  app.enableCors({
    origin: config.get<string[]>('app.corsOrigins'),
    credentials: true,
  });
  app.useGlobalPipes(
    new ValidationPipe({
      transform: true,
      whitelist: true,
      forbidNonWhitelisted: false,
      transformOptions: { enableImplicitConversion: true },
    }),
  );

  const swagger = new DocumentBuilder()
    .setTitle('CG CARGA TMS API')
    .setDescription('Gestion de transporte y control de entregas en tiempo real')
    .setVersion('0.1')
    .addBearerAuth()
    .build();
  SwaggerModule.setup('api/docs', app, SwaggerModule.createDocument(app, swagger));

  const port = config.get<number>('app.port') ?? 3001;
  await app.listen(port, '0.0.0.0');
  new Logger('Bootstrap').log(`API en http://localhost:${port}/api (docs en /api/docs)`);
}

void bootstrap();
