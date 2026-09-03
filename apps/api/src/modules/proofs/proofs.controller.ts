import {
  Body,
  Controller,
  Get,
  Param,
  Post,
  UploadedFile,
  UseInterceptors,
} from '@nestjs/common';
import { FileInterceptor } from '@nestjs/platform-express';
import { ApiConsumes, ApiOperation, ApiTags } from '@nestjs/swagger';
import { ProofType } from '@prisma/client';
import { IsDateString, IsEnum, IsNumber, IsOptional, IsString, IsUUID } from 'class-validator';
import { ProofsService } from './proofs.service';

class RequestUploadDto {
  @IsOptional() @IsString() extension?: string;
}

class ConfirmUploadDto {
  @IsString() objectKey!: string;
  @IsString() mimeType!: string;
  @IsNumber() sizeBytes!: number;
  @IsOptional() @IsString() checksum?: string;
  @IsOptional() @IsEnum(ProofType) type?: ProofType;
  @IsOptional() @IsUUID() driverId?: string;
  @IsOptional() @IsNumber() lat?: number;
  @IsOptional() @IsNumber() lng?: number;
  @IsOptional() @IsString() note?: string;
  @IsDateString() capturedAt!: string;
}

@ApiTags('pod')
@Controller('orders/:orderId/proofs')
export class ProofsController {
  constructor(private readonly proofs: ProofsService) {}

  @Get()
  list(@Param('orderId') orderId: string) {
    return this.proofs.listByOrder(orderId);
  }

  @Post('presign')
  @ApiOperation({ summary: 'URL prefirmada de MinIO para subir la foto' })
  presign(@Param('orderId') orderId: string, @Body() dto: RequestUploadDto) {
    return this.proofs.requestUpload(orderId, dto.extension);
  }

  @Post('confirm')
  @ApiOperation({ summary: 'Confirma la subida y registra la evidencia' })
  confirm(@Param('orderId') orderId: string, @Body() dto: ConfirmUploadDto) {
    return this.proofs.confirmUpload({
      ...dto,
      orderId,
      capturedAt: new Date(dto.capturedAt),
    });
  }

  @Post('upload')
  @ApiConsumes('multipart/form-data')
  @ApiOperation({ summary: 'Sube la foto a traves del API (fallback sin acceso directo a MinIO)' })
  @UseInterceptors(FileInterceptor('file'))
  upload(
    @Param('orderId') orderId: string,
    @UploadedFile() file: Express.Multer.File,
    @Body() body: { driverId?: string; lat?: string; lng?: string; note?: string; capturedAt?: string; type?: ProofType },
  ) {
    return this.proofs.uploadDirect(orderId, file, {
      driverId: body.driverId,
      lat: body.lat ? Number(body.lat) : undefined,
      lng: body.lng ? Number(body.lng) : undefined,
      note: body.note,
      type: body.type,
      capturedAt: body.capturedAt ? new Date(body.capturedAt) : new Date(),
    });
  }
}
