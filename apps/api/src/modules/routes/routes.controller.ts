import { Body, Controller, Get, Param, Post, Query } from '@nestjs/common';
import { ApiOperation, ApiTags } from '@nestjs/swagger';
import { IsLatitude, IsLongitude, IsUUID } from 'class-validator';
import { RoutesService } from './routes.service';

class AssignDriverDto {
  @IsUUID() driverId!: string;
}

class OptimizeDto {
  @IsLatitude() startLat!: number;
  @IsLongitude() startLng!: number;
}

@ApiTags('routes')
@Controller('routes')
export class RoutesController {
  constructor(private readonly routes: RoutesService) {}

  @Get()
  @ApiOperation({ summary: 'Rutas y ordenes de una fecha de despacho' })
  findAll(@Query('date') date?: string) {
    return this.routes.findByDate(date);
  }

  @Get('geojson')
  @ApiOperation({ summary: 'FeatureCollection para los marcadores de Leaflet' })
  geojson(@Query('date') date?: string) {
    return this.routes.findAsGeoJson(date);
  }

  @Get('summary')
  @ApiOperation({ summary: 'KPIs del dashboard' })
  summary(@Query('date') date?: string) {
    return this.routes.summary(date);
  }

  @Get('viewport')
  @ApiOperation({ summary: 'Ordenes dentro del bounding box del mapa' })
  viewport(
    @Query('south') south: string,
    @Query('west') west: string,
    @Query('north') north: string,
    @Query('east') east: string,
    @Query('date') date?: string,
  ) {
    return this.routes.findInBoundingBox(
      { south: Number(south), west: Number(west), north: Number(north), east: Number(east) },
      date,
    );
  }

  @Post(':id/driver')
  assignDriver(@Param('id') id: string, @Body() dto: AssignDriverDto) {
    return this.routes.assignDriver(id, dto.driverId);
  }

  @Post(':id/optimize')
  @ApiOperation({ summary: 'Secuencia las paradas por vecino mas cercano (PostGIS)' })
  optimize(@Param('id') id: string, @Body() dto: OptimizeDto) {
    return this.routes.optimizeSequence(id, dto.startLat, dto.startLng);
  }
}
