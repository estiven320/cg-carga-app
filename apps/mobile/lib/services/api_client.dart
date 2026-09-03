import 'dart:convert';
import 'dart:io';
import 'package:crypto/crypto.dart';
import 'package:http/http.dart' as http;
import '../config.dart';
import '../models/delivery.dart';

/// Cliente HTTP del API de despacho.
class ApiClient {
  ApiClient({http.Client? client}) : _client = client ?? http.Client();

  final http.Client _client;
  String? _token;
  String? driverId;

  Map<String, String> get _headers => {
        'Content-Type': 'application/json',
        if (_token != null) 'Authorization': 'Bearer $_token',
      };

  Future<void> login(String documentNumber, String phone) async {
    final response = await _client.post(
      Uri.parse('${AppConfig.apiUrl}/auth/driver/login'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({'documentNumber': documentNumber, 'phone': phone}),
    );
    if (response.statusCode >= 400) {
      throw Exception('Credenciales invalidas');
    }
    final body = jsonDecode(response.body) as Map<String, dynamic>;
    _token = body['accessToken'] as String;
    driverId = (body['driver'] as Map<String, dynamic>)['id'] as String;
  }

  Future<List<DriverRoute>> fetchRoutes(DateTime date) async {
    final iso = date.toIso8601String().substring(0, 10);
    final response = await _client.get(
      Uri.parse('${AppConfig.apiUrl}/routes?date=$iso'),
      headers: _headers,
    );
    if (response.statusCode >= 400) throw Exception('No se pudieron cargar las rutas');

    final data = jsonDecode(response.body) as List<dynamic>;
    return data
        .map((item) => DriverRoute.fromJson(item as Map<String, dynamic>))
        .where((route) => route.deliveries.isNotEmpty)
        .toList();
  }

  Future<void> updateStatus(
    String orderId,
    String status, {
    double? lat,
    double? lng,
    String? note,
    String? failureReason,
    String? receivedBy,
  }) async {
    final response = await _client.patch(
      Uri.parse('${AppConfig.apiUrl}/orders/$orderId/status'),
      headers: _headers,
      body: jsonEncode({
        'status': status,
        if (lat != null) 'lat': lat,
        if (lng != null) 'lng': lng,
        if (note != null) 'note': note,
        if (failureReason != null) 'failureReason': failureReason,
        if (receivedBy != null) 'receivedBy': receivedBy,
      }),
    );
    if (response.statusCode >= 400) {
      throw Exception('No se pudo actualizar el estado: ${response.body}');
    }
  }

  /// Sube la evidencia fotografica a MinIO en tres pasos.
  ///
  ///   1. El API emite una URL prefirmada (PUT) — el binario no pasa por NestJS.
  ///   2. La foto va DIRECTO al bucket de MinIO.
  ///   3. Se confirma al API, que verifica que el objeto exista y lo registra.
  ///
  /// El SHA-256 de la foto viaja en la confirmacion: si la app reintenta tras
  /// perder senal, el backend reconoce la evidencia y no la duplica.
  Future<void> uploadProof(
    String orderId,
    File photo, {
    double? lat,
    double? lng,
    String? note,
  }) async {
    final bytes = await photo.readAsBytes();
    final checksum = sha256.convert(bytes).toString();
    final extension = photo.path.split('.').last.toLowerCase();

    // 1. URL prefirmada
    final presignResponse = await _client.post(
      Uri.parse('${AppConfig.apiUrl}/orders/$orderId/proofs/presign'),
      headers: _headers,
      body: jsonEncode({'extension': extension}),
    );
    if (presignResponse.statusCode >= 400) {
      throw Exception('No se pudo preparar la subida');
    }
    final presign = jsonDecode(presignResponse.body) as Map<String, dynamic>;

    // 2. Subida directa a MinIO
    final uploadResponse = await _client.put(
      Uri.parse(presign['uploadUrl'] as String),
      headers: {'Content-Type': 'image/$extension'},
      body: bytes,
    );
    if (uploadResponse.statusCode >= 400) {
      throw Exception('Fallo la subida de la foto (${uploadResponse.statusCode})');
    }

    // 3. Confirmacion
    final confirmResponse = await _client.post(
      Uri.parse('${AppConfig.apiUrl}/orders/$orderId/proofs/confirm'),
      headers: _headers,
      body: jsonEncode({
        'objectKey': presign['objectKey'],
        'mimeType': 'image/$extension',
        'sizeBytes': bytes.length,
        'checksum': checksum,
        'type': 'PHOTO',
        if (driverId != null) 'driverId': driverId,
        if (lat != null) 'lat': lat,
        if (lng != null) 'lng': lng,
        if (note != null) 'note': note,
        'capturedAt': DateTime.now().toUtc().toIso8601String(),
      }),
    );
    if (confirmResponse.statusCode >= 400) {
      throw Exception('No se pudo registrar la evidencia');
    }
  }

  Future<void> sendPing({
    required double lat,
    required double lng,
    String? routeId,
    double? speedKmh,
    double? accuracyM,
  }) async {
    if (driverId == null) return;
    await _client.post(
      Uri.parse('${AppConfig.apiUrl}/drivers/$driverId/ping'),
      headers: _headers,
      body: jsonEncode({
        'lat': lat,
        'lng': lng,
        if (routeId != null) 'routeId': routeId,
        if (speedKmh != null) 'speedKmh': speedKmh,
        if (accuracyM != null) 'accuracyM': accuracyM,
        'recordedAt': DateTime.now().toUtc().toIso8601String(),
      }),
    );
  }
}
