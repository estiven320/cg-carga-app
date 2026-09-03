import { Module } from '@nestjs/common';
import { MulterModule } from '@nestjs/platform-express';
import { memoryStorage } from 'multer';
import { GeocodingModule } from '../geocoding/geocoding.module';
import { DispatchImportService } from './dispatch-import.service';
import { ExcelParserService } from './excel-parser.service';
import { ImportController } from './import.controller';

@Module({
  imports: [
    GeocodingModule,
    // El Excel se procesa en memoria: nunca toca disco, evita limpieza de temp.
    MulterModule.register({ storage: memoryStorage() }),
  ],
  controllers: [ImportController],
  providers: [DispatchImportService, ExcelParserService],
  exports: [DispatchImportService, ExcelParserService],
})
export class ImportModule {}
