import { Body, Controller, Get, Param, Post, Query } from '@nestjs/common';
import { ApiTags } from '@nestjs/swagger';
import { IsNumber, IsOptional, IsString } from 'class-validator';
import { DriversService } from './drivers.service';

class PingDto {
  @IsNumber() lat!: number;
  @IsNumber() lng!: number;
  @IsOptional() @IsString() routeId?: string;
  @IsOptional() @IsNumber() accuracyM?: number;
  @IsOptional() @IsNumber() speedKmh?: number;
  @IsOptional() @IsNumber() batteryPct?: number;
  @IsOptional() @IsString() recordedAt?: string;
}

@ApiTags('drivers')
@Controller('drivers')
export class DriversController {
  constructor(private readonly drivers: DriversService) {}

  @Get()
  findAll(@Query('all') all?: string) {
    return this.drivers.findAll(all !== 'true');
  }

  @Post(':id/ping')
  ping(@Param('id') id: string, @Body() dto: PingDto) {
    return this.drivers.recordPing({
      driverId: id,
      routeId: dto.routeId,
      lat: dto.lat,
      lng: dto.lng,
      accuracyM: dto.accuracyM,
      speedKmh: dto.speedKmh,
      batteryPct: dto.batteryPct,
      recordedAt: dto.recordedAt ? new Date(dto.recordedAt) : new Date(),
    });
  }

  @Get(':id/track')
  track(@Param('id') id: string, @Query('from') from?: string, @Query('to') to?: string) {
    const start = from ? new Date(from) : new Date(new Date().setHours(0, 0, 0, 0));
    const end = to ? new Date(to) : new Date();
    return this.drivers.track(id, start, end);
  }
}
