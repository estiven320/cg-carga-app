import { Module, type Provider } from '@nestjs/common';
import { ConfigService } from '@nestjs/config';
import { NotificationsController } from './notifications.controller';
import { NotificationsService } from './notifications.service';
import { WHATSAPP_PROVIDER } from './whatsapp.token';
import {
  BaileysProvider,
  DisabledWhatsappProvider,
  EvolutionApiProvider,
  type WhatsappProvider,
} from './whatsapp.provider';

export { WHATSAPP_PROVIDER } from './whatsapp.token';

/**
 * El proveedor concreto se elige por configuracion, no por codigo: cambiar de
 * Evolution a Baileys (o apagar los envios en desarrollo) es una variable de
 * entorno, sin recompilar ni tocar los servicios que notifican.
 */
const whatsappProvider: Provider = {
  provide: WHATSAPP_PROVIDER,
  inject: [ConfigService],
  useFactory: (config: ConfigService): WhatsappProvider => {
    switch (config.get<string>('whatsapp.provider')) {
      case 'evolution':
        return new EvolutionApiProvider(config);
      case 'baileys':
        return new BaileysProvider(config);
      default:
        return new DisabledWhatsappProvider();
    }
  },
};

@Module({
  controllers: [NotificationsController],
  providers: [NotificationsService, whatsappProvider],
  exports: [NotificationsService],
})
export class NotificationsModule {}
