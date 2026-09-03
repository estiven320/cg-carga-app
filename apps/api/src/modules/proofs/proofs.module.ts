import { Module } from '@nestjs/common';
import { MulterModule } from '@nestjs/platform-express';
import { memoryStorage } from 'multer';
import { ProofsController } from './proofs.controller';
import { ProofsService } from './proofs.service';

@Module({
  imports: [MulterModule.register({ storage: memoryStorage(), limits: { fileSize: 15 * 1024 * 1024 } })],
  controllers: [ProofsController],
  providers: [ProofsService],
  exports: [ProofsService],
})
export class ProofsModule {}
