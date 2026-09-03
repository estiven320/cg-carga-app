import { Injectable, Logger } from '@nestjs/common';
import { ConfigService } from '@nestjs/config';
import { request } from 'undici';
import type { WhatsappConfig } from '../../config/configuration';

export interface SendResult {
  ok: boolean;
  providerMessageId?: string;
  error?: string;
}

export interface WhatsappProvider {
  readonly name: string;
  send(to: string, message: string): Promise<SendResult>;
  isReady(): Promise<boolean>;
}

/**
 * Normaliza a E.164 sin '+': Evolution y Baileys esperan "573001112233@s.whatsapp.net".
 * Los telefonos del maestro de conductores llegan como "3001112233" o
 * "300 111 2233", asi que se antepone el indicativo por defecto.
 */
export function toWhatsappNumber(phone: string, defaultCountryCode: string): string {
  const digits = String(phone ?? '').replace(/\D/g, '');
  if (!digits) throw new Error('Telefono vacio');
  if (digits.startsWith(defaultCountryCode) && digits.length > 10) return digits;
  if (digits.length === 10) return `${defaultCountryCode}${digits}`;
  return digits;
}

/**
 * Evolution API: gateway open source sobre WhatsApp Web. Es el proveedor por
 * defecto porque corre en su propio contenedor, sobrevive a los reinicios del
 * API y expone REST simple, sin costo de licencia (a diferencia de la Cloud API
 * oficial, que cobra por conversacion).
 */
@Injectable()
export class EvolutionApiProvider implements WhatsappProvider {
  readonly name = 'evolution';
  private readonly logger = new Logger(EvolutionApiProvider.name);
  private readonly config: WhatsappConfig;

  constructor(configService: ConfigService) {
    this.config = configService.getOrThrow<WhatsappConfig>('whatsapp');
  }

  async isReady(): Promise<boolean> {
    try {
      const response = await request(
        `${this.config.evolutionApiUrl}/instance/connectionState/${this.config.evolutionInstance}`,
        { headers: { apikey: this.config.evolutionApiKey } },
      );
      if (response.statusCode >= 400) {
        response.body.dump();
        return false;
      }
      const body = (await response.body.json()) as any;
      return body?.instance?.state === 'open' || body?.state === 'open';
    } catch (error) {
      this.logger.warn(`Evolution API no responde: ${(error as Error).message}`);
      return false;
    }
  }

  async send(to: string, message: string): Promise<SendResult> {
    try {
      const number = toWhatsappNumber(to, this.config.defaultCountryCode);
      const response = await request(
        `${this.config.evolutionApiUrl}/message/sendText/${this.config.evolutionInstance}`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            apikey: this.config.evolutionApiKey,
          },
          body: JSON.stringify({ number, text: message }),
        },
      );

      const body = (await response.body.json().catch(() => ({}))) as any;
      if (response.statusCode >= 400) {
        return { ok: false, error: `HTTP ${response.statusCode}: ${JSON.stringify(body).slice(0, 200)}` };
      }
      return { ok: true, providerMessageId: body?.key?.id ?? body?.messageId };
    } catch (error) {
      return { ok: false, error: (error as Error).message };
    }
  }
}

/**
 * Baileys embebido: alternativa sin contenedor extra. Mantiene el socket de
 * WhatsApp Web dentro del proceso de NestJS.
 *
 * Compromiso a tener presente: la sesion vive en el mismo proceso, asi que un
 * redeploy del API desconecta el numero hasta que se reconecte con la sesion
 * persistida en `BAILEYS_SESSION_PATH`. Por eso Evolution es el default y esto
 * queda como opcion para despliegues de una sola maquina.
 *
 * Requiere instalar la dependencia opcional:
 *   npm i @whiskeysockets/baileys qrcode-terminal --workspace=apps/api
 */
@Injectable()
export class BaileysProvider implements WhatsappProvider {
  readonly name = 'baileys';
  private readonly logger = new Logger(BaileysProvider.name);
  private readonly config: WhatsappConfig;
  private socket: any = null;
  private connected = false;

  constructor(configService: ConfigService) {
    this.config = configService.getOrThrow<WhatsappConfig>('whatsapp');
  }

  async connect(): Promise<void> {
    if (this.socket) return;
    try {
      // Import dinamico: si la dependencia opcional no esta instalada, el API
      // arranca igual y solo queda deshabilitado este proveedor.
      const baileys = await import('@whiskeysockets/baileys' as string);
      const { default: makeWASocket, useMultiFileAuthState, DisconnectReason } = baileys as any;

      const { state, saveCreds } = await useMultiFileAuthState(this.config.baileysSessionPath);
      this.socket = makeWASocket({ auth: state, printQRInTerminal: true });

      this.socket.ev.on('creds.update', saveCreds);
      this.socket.ev.on('connection.update', (update: any) => {
        const { connection, lastDisconnect } = update;
        this.connected = connection === 'open';
        if (connection === 'close') {
          const shouldReconnect =
            lastDisconnect?.error?.output?.statusCode !== DisconnectReason.loggedOut;
          this.logger.warn(`Baileys desconectado. Reconectar: ${shouldReconnect}`);
          this.socket = null;
          if (shouldReconnect) void this.connect();
        }
      });
    } catch (error) {
      this.logger.error(
        `No se pudo iniciar Baileys (instale @whiskeysockets/baileys): ${(error as Error).message}`,
      );
    }
  }

  async isReady(): Promise<boolean> {
    if (!this.socket) await this.connect();
    return this.connected;
  }

  async send(to: string, message: string): Promise<SendResult> {
    if (!(await this.isReady())) return { ok: false, error: 'Baileys no conectado' };
    try {
      const jid = `${toWhatsappNumber(to, this.config.defaultCountryCode)}@s.whatsapp.net`;
      const sent = await this.socket.sendMessage(jid, { text: message });
      return { ok: true, providerMessageId: sent?.key?.id };
    } catch (error) {
      return { ok: false, error: (error as Error).message };
    }
  }
}

/** Proveedor nulo: registra el mensaje sin enviarlo. Util en desarrollo. */
@Injectable()
export class DisabledWhatsappProvider implements WhatsappProvider {
  readonly name = 'disabled';
  private readonly logger = new Logger(DisabledWhatsappProvider.name);

  async isReady(): Promise<boolean> {
    return false;
  }

  async send(to: string, message: string): Promise<SendResult> {
    this.logger.log(`[WhatsApp deshabilitado] Para ${to}: ${message.slice(0, 120)}...`);
    return { ok: false, error: 'WHATSAPP_PROVIDER=disabled' };
  }
}
