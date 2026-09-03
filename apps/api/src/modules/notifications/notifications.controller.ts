import { Body, Controller, Get, Param, Post } from '@nestjs/common';
import { ApiOperation, ApiTags } from '@nestjs/swagger';
import { IsOptional, IsString } from 'class-validator';
import { NotificationsService } from './notifications.service';

class SendRouteDto {
  @IsOptional() @IsString() appUrl?: string;
}

class SendAlertDto {
  @IsString() phone!: string;
  @IsString() message!: string;
  @IsOptional() @IsString() routeId?: string;
}

@ApiTags('notifications')
@Controller('notifications')
export class NotificationsController {
  constructor(private readonly notifications: NotificationsService) {}

  @Get('status')
  status() {
    return this.notifications.status();
  }

  @Post('routes/:routeId/send')
  @ApiOperation({ summary: 'Envia la ruta al conductor por WhatsApp' })
  sendRoute(@Param('routeId') routeId: string, @Body() dto: SendRouteDto) {
    return this.notifications.sendRouteToDriver(routeId, dto.appUrl);
  }

  @Post('alerts')
  sendAlert(@Body() dto: SendAlertDto) {
    return this.notifications.sendAlert(dto.phone, dto.message, dto.routeId);
  }

  @Post('retry')
  retry() {
    return this.notifications.retryQueued();
  }
}
