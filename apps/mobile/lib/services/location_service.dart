import 'dart:async';
import 'package:geolocator/geolocator.dart';
import '../config.dart';
import 'api_client.dart';

/// Reporte periodico de posicion mientras la ruta esta en curso.
///
/// Los envios fallidos se ignoran a proposito: la posicion es un dato efimero
/// (el siguiente ping la reemplaza en 30 s) y reintentarla solo gastaria bateria
/// y datos del conductor. Lo que SI se encola offline es la evidencia POD.
class LocationService {
  LocationService(this._api);

  final ApiClient _api;
  Timer? _timer;
  String? _routeId;

  Future<bool> ensurePermission() async {
    if (!await Geolocator.isLocationServiceEnabled()) return false;

    var permission = await Geolocator.checkPermission();
    if (permission == LocationPermission.denied) {
      permission = await Geolocator.requestPermission();
    }
    return permission == LocationPermission.always ||
        permission == LocationPermission.whileInUse;
  }

  Future<Position?> current() async {
    if (!await ensurePermission()) return null;
    return Geolocator.getCurrentPosition(
      locationSettings: const LocationSettings(accuracy: LocationAccuracy.high),
    );
  }

  void startTracking(String routeId) {
    _routeId = routeId;
    _timer?.cancel();
    _timer = Timer.periodic(AppConfig.pingInterval, (_) async {
      final position = await current();
      if (position == null) return;
      try {
        await _api.sendPing(
          lat: position.latitude,
          lng: position.longitude,
          routeId: _routeId,
          speedKmh: position.speed * 3.6,
          accuracyM: position.accuracy,
        );
      } catch (_) {
        // Ver nota de la clase: un ping perdido no se reintenta.
      }
    });
  }

  void stopTracking() {
    _timer?.cancel();
    _timer = null;
  }
}
