import { Body, Controller, Get, Param, Patch, Post } from '@nestjs/common';
import { ApiOperation, ApiTags } from '@nestjs/swagger';
import { OrderStatus } from '@prisma/client';
import { IsArray, IsEnum, IsOptional, IsString, IsNumber } from 'class-validator';
import { OrdersService } from './orders.service';

class UpdateStatusDto {
  @IsEnum(OrderStatus) status!: OrderStatus;
  @IsOptional() @IsNumber() lat?: number;
  @IsOptional() @IsNumber() lng?: number;
  @IsOptional() @IsString() note?: string;
  @IsOptional() @IsString() failureReason?: string;
  @IsOptional() @IsString() receivedBy?: string;
  @IsOptional() @IsString() receivedByDocument?: string;
}

class ReorderDto {
  @IsArray() @IsString({ each: true }) orderIds!: string[];
}

@ApiTags('orders')
@Controller('orders')
export class OrdersController {
  constructor(private readonly orders: OrdersService) {}

  @Get(':id')
  findOne(@Param('id') id: string) {
    return this.orders.findOne(id);
  }

  @Patch(':id/status')
  @ApiOperation({ summary: 'Actualiza el estado de una entrega' })
  updateStatus(@Param('id') id: string, @Body() dto: UpdateStatusDto) {
    return this.orders.updateStatus(id, dto);
  }

  @Post('routes/:routeId/reorder')
  reorder(@Param('routeId') routeId: string, @Body() dto: ReorderDto) {
    return this.orders.reorder(routeId, dto.orderIds);
  }
}
