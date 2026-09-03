import { Body, Controller, Get, Param, Post, Query } from '@nestjs/common';
import { ApiOperation, ApiTags } from '@nestjs/swagger';
import { IsLatitude, IsLongitude, IsOptional, IsString } from 'class-validator';
import { GeocodingService } from './geocoding.service';

class ManualCoordinatesDto {
  @IsLatitude() lat!: number;
  @IsLongitude() lng!: number;
}

class GeocodePreviewDto {
  @IsString() address!: string;
  @IsOptional() @IsString() locality?: string;
}

@ApiTags('geocoding')
@Controller('geocoding')
export class GeocodingController {
  constructor(private readonly geocoding: GeocodingService) {}

  @Get('health')
  @ApiOperation({ summary: 'Estado del cache y de la cola de Nominatim' })
  health() {
    return this.geocoding.health();
  }

  @Post('preview')
  @ApiOperation({ summary: 'Geocodifica una direccion suelta (usa cache)' })
  preview(@Body() dto: GeocodePreviewDto) {
    return this.geocoding.geocode(dto.address, dto.locality);
  }

  @Post('orders/:id/coordinates')
  @ApiOperation({ summary: 'Corrige manualmente la coordenada de una orden' })
  async setManual(@Param('id') id: string, @Body() dto: ManualCoordinatesDto) {
    await this.geocoding.setManualCoordinates(id, dto.lat, dto.lng);
    return { ok: true };
  }

  @Post('retry')
  @ApiOperation({ summary: 'Reintenta las ordenes sin coordenada' })
  retry(@Query('date') date?: string) {
    return this.geocoding.retryFailedOrders(date ? new Date(date) : undefined);
  }
}
