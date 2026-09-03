import { Module } from '@nestjs/common';
import { ConfigModule } from '@nestjs/config';
import { ThrottlerGuard, ThrottlerModule } from '@nestjs/throttler';
import { APP_GUARD } from '@nestjs/core';
import configuration from './config/configuration';
import { ProgressBusModule } from './common/events/progress.bus';
import { PrismaModule } from './prisma/prisma.module';
import { AuthModule } from './modules/auth/auth.module';
import { DriversModule } from './modules/drivers/drivers.module';
import { GeocodingModule } from './modules/geocoding/geocoding.module';
import { ImportModule } from './modules/import/import.module';
import { NotificationsModule } from './modules/notifications/notifications.module';
import { OrdersModule } from './modules/orders/orders.module';
import { ProofsModule } from './modules/proofs/proofs.module';
import { RealtimeModule } from './modules/realtime/realtime.module';
import { RoutesModule } from './modules/routes/routes.module';
import { StorageModule } from './modules/storage/storage.module';

@Module({
  imports: [
    ConfigModule.forRoot({ isGlobal: true, load: [configuration], envFilePath: ['.env', '../../.env'] }),
    // Protege el API publico; el rate limit de Nominatim es aparte (ver
    // NominatimQueue) porque es una restriccion de salida, no de entrada.
    ThrottlerModule.forRoot([{ ttl: 60_000, limit: 300 }]),
    ProgressBusModule,
    PrismaModule,
    StorageModule,
    AuthModule,
    GeocodingModule,
    ImportModule,
    RoutesModule,
    OrdersModule,
    ProofsModule,
    DriversModule,
    NotificationsModule,
    RealtimeModule,
  ],
  providers: [{ provide: APP_GUARD, useClass: ThrottlerGuard }],
})
export class AppModule {}
