import {
  BadRequestException,
  Controller,
  Get,
  Param,
  Post,
  Query,
  UploadedFile,
  UseInterceptors,
} from '@nestjs/common';
import { FileInterceptor } from '@nestjs/platform-express';
import { ConfigService } from '@nestjs/config';
import { ApiConsumes, ApiOperation, ApiTags } from '@nestjs/swagger';
import { DispatchImportService } from './dispatch-import.service';

const XLSX_MIME = [
  'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
  'application/vnd.ms-excel',
  'application/octet-stream',
];

@ApiTags('import')
@Controller('import')
export class ImportController {
  constructor(
    private readonly importService: DispatchImportService,
    private readonly config: ConfigService,
  ) {}

  @Post('dispatch')
  @ApiConsumes('multipart/form-data')
  @ApiOperation({ summary: 'Sube el Excel de programacion y crea rutas + ordenes' })
  @UseInterceptors(FileInterceptor('file'))
  async importDispatch(
    @UploadedFile() file: Express.Multer.File,
    @Query('sheet') sheet?: string,
    @Query('date') date?: string,
    @Query('geocode') geocode?: string,
  ) {
    this.assertFile(file);
    return this.importService.importFile(file, {
      sheetName: sheet,
      dispatchDate: date ? new Date(`${date}T00:00:00.000Z`) : undefined,
      geocode: geocode !== 'false',
    });
  }

  @Post('sheets')
  @ApiConsumes('multipart/form-data')
  @ApiOperation({ summary: 'Lista las hojas del archivo sin importarlo' })
  @UseInterceptors(FileInterceptor('file'))
  async listSheets(@UploadedFile() file: Express.Multer.File) {
    this.assertFile(file);
    return { sheets: await this.importService.listSheets(file.buffer) };
  }

  @Get('batches/:id')
  @ApiOperation({ summary: 'Estado de un lote de importacion' })
  getBatch(@Param('id') id: string) {
    return this.importService.getBatch(id);
  }

  @Post('batches/:id/geocode')
  @ApiOperation({ summary: 'Relanza la geocodificacion pendiente del lote' })
  geocode(@Param('id') id: string) {
    return this.importService.geocodeBatch(id);
  }

  private assertFile(file?: Express.Multer.File): asserts file is Express.Multer.File {
    if (!file) throw new BadRequestException('Debe adjuntar el archivo en el campo "file".');

    const maxMb = this.config.get<number>('import.maxFileMb') ?? 25;
    if (file.size > maxMb * 1024 * 1024) {
      throw new BadRequestException(`El archivo supera el limite de ${maxMb} MB.`);
    }
    if (!XLSX_MIME.includes(file.mimetype) && !/\.xlsx?$/i.test(file.originalname)) {
      throw new BadRequestException('Formato no soportado. Se espera un archivo .xlsx');
    }
  }
}
