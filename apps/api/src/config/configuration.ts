export interface AppConfig {
  port: number;
  nodeEnv: string;
  corsOrigins: string[];
  jwtSecret: string;
  jwtExpiresIn: string;
}

export interface NominatimConfig {
  baseUrl: string;
  userAgent: string;
  email?: string;
  /**
   * Intervalo minimo entre peticiones. La politica de uso publico de OSM exige
   * un maximo de 1 req/s absoluto; usamos 1100 ms de colchon por defecto.
   * @see https://operations.osmfoundation.org/policies/nominatim/
   */
  minIntervalMs: number;
  timeoutMs: number;
  maxRetries: number;
  countryCodes: string;
  countrySuffix: string;
  cacheTtlDays: number;
}

export interface MinioConfig {
  endPoint: string;
  port: number;
  useSSL: boolean;
  accessKey: string;
  secretKey: string;
  bucket: string;
  region: string;
  publicUrl: string;
  presignExpirySeconds: number;
}

export interface WhatsappConfig {
  provider: 'evolution' | 'baileys' | 'disabled';
  evolutionApiUrl: string;
  evolutionApiKey: string;
  evolutionInstance: string;
  defaultCountryCode: string;
  baileysSessionPath: string;
}

export interface ImportConfig {
  defaultSheet: string;
  maxFileMb: number;
}

const int = (value: string | undefined, fallback: number): number => {
  const parsed = Number.parseInt(value ?? '', 10);
  return Number.isFinite(parsed) ? parsed : fallback;
};

const bool = (value: string | undefined, fallback = false): boolean =>
  value === undefined ? fallback : ['1', 'true', 'yes'].includes(value.toLowerCase());

export default () => ({
  app: {
    port: int(process.env.PORT, 3001),
    nodeEnv: process.env.NODE_ENV ?? 'development',
    corsOrigins: (process.env.CORS_ORIGINS ?? 'http://localhost:3000')
      .split(',')
      .map((origin) => origin.trim())
      .filter(Boolean),
    jwtSecret: process.env.JWT_SECRET ?? 'dev-secret-cambiar',
    jwtExpiresIn: process.env.JWT_EXPIRES_IN ?? '12h',
  } satisfies AppConfig,

  nominatim: {
    baseUrl: (process.env.NOMINATIM_BASE_URL ?? 'https://nominatim.openstreetmap.org').replace(/\/$/, ''),
    userAgent: process.env.NOMINATIM_USER_AGENT ?? 'CG-CARGA-TMS/0.1 (contacto@cgcarga.co)',
    email: process.env.NOMINATIM_EMAIL,
    minIntervalMs: int(process.env.NOMINATIM_MIN_INTERVAL_MS, 1100),
    timeoutMs: int(process.env.NOMINATIM_TIMEOUT_MS, 10_000),
    maxRetries: int(process.env.NOMINATIM_MAX_RETRIES, 3),
    countryCodes: process.env.NOMINATIM_COUNTRY_CODES ?? 'co',
    countrySuffix: process.env.NOMINATIM_COUNTRY_SUFFIX ?? 'Colombia',
    cacheTtlDays: int(process.env.GEOCODE_CACHE_TTL_DAYS, 180),
  } satisfies NominatimConfig,

  minio: {
    endPoint: process.env.MINIO_ENDPOINT ?? 'localhost',
    port: int(process.env.MINIO_PORT, 9000),
    useSSL: bool(process.env.MINIO_USE_SSL, false),
    accessKey: process.env.MINIO_ACCESS_KEY ?? 'cgcarga',
    secretKey: process.env.MINIO_SECRET_KEY ?? 'cgcarga-secret',
    bucket: process.env.MINIO_BUCKET ?? 'pod',
    region: process.env.MINIO_REGION ?? 'us-east-1',
    publicUrl: (process.env.MINIO_PUBLIC_URL ?? 'http://localhost:9000').replace(/\/$/, ''),
    presignExpirySeconds: int(process.env.MINIO_PRESIGN_EXPIRY_SECONDS, 3600),
  } satisfies MinioConfig,

  whatsapp: {
    provider: (process.env.WHATSAPP_PROVIDER ?? 'disabled') as WhatsappConfig['provider'],
    evolutionApiUrl: (process.env.EVOLUTION_API_URL ?? 'http://localhost:8080').replace(/\/$/, ''),
    evolutionApiKey: process.env.EVOLUTION_API_KEY ?? '',
    evolutionInstance: process.env.EVOLUTION_INSTANCE ?? 'cgcarga',
    defaultCountryCode: process.env.WHATSAPP_DEFAULT_COUNTRY_CODE ?? '57',
    baileysSessionPath: process.env.BAILEYS_SESSION_PATH ?? './.baileys-session',
  } satisfies WhatsappConfig,

  import: {
    defaultSheet: process.env.IMPORT_DEFAULT_SHEET ?? 'PROGRAMACION 3 DE SEPTIEMBRE',
    maxFileMb: int(process.env.IMPORT_MAX_FILE_MB, 25),
  } satisfies ImportConfig,
});
