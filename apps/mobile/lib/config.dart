/// Configuracion en tiempo de compilacion.
///
///   flutter run --dart-define=API_URL=http://10.0.2.2:3001/api
///
/// 10.0.2.2 es el host de la maquina desde el emulador de Android.
class AppConfig {
  static const apiUrl = String.fromEnvironment(
    'API_URL',
    defaultValue: 'http://10.0.2.2:3001/api',
  );

  static const tileUrl = String.fromEnvironment(
    'TILE_URL',
    defaultValue: 'https://tile.openstreetmap.org/{z}/{x}/{y}.png',
  );

  /// Requerido por la politica de uso de los tiles de OSM.
  static const userAgent = 'co.cgcarga.driver';

  /// Cada cuanto se reporta la posicion al backend.
  static const pingInterval = Duration(seconds: 30);
}
