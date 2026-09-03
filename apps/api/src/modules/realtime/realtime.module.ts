import { Module } from '@nestjs/common';
import { DriversModule } from '../drivers/drivers.module';
import { RealtimeGateway } from './realtime.gateway';

@Module({
  imports: [DriversModule],
  providers: [RealtimeGateway],
})
export class RealtimeModule {}
