import { Module } from '@nestjs/common';
import { GeocodingController } from './geocoding.controller';
import { GeocodingService } from './geocoding.service';
import { NominatimClient } from './nominatim.client';
import { NominatimQueue } from './nominatim.queue';

@Module({
  controllers: [GeocodingController],
  providers: [GeocodingService, NominatimClient, NominatimQueue],
  exports: [GeocodingService, NominatimQueue],
})
export class GeocodingModule {}
