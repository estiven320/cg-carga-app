import 'dart:io';
import 'package:flutter/material.dart';
import 'package:flutter_map/flutter_map.dart';
import 'package:image_picker/image_picker.dart';
import 'package:latlong2/latlong.dart';
import '../config.dart';
import '../models/delivery.dart';
import '../services/api_client.dart';
import '../services/location_service.dart';
import '../theme.dart';

/// Pantalla de entrega: es donde el conductor cierra el ciclo.
///
/// Reglas de negocio que aplica:
///  - No se puede marcar ENTREGADA sin al menos una foto de soporte (POD).
///  - La coordenada del GPS viaja con la evidencia, para que el despachador
///    pueda auditar donde se tomo realmente la foto.
class DeliveryScreen extends StatefulWidget {
  const DeliveryScreen({
    super.key,
    required this.api,
    required this.location,
    required this.delivery,
  });

  final ApiClient api;
  final LocationService location;
  final Delivery delivery;

  @override
  State<DeliveryScreen> createState() => _DeliveryScreenState();
}

class _DeliveryScreenState extends State<DeliveryScreen> {
  final _photos = <File>[];
  final _receivedBy = TextEditingController();
  final _note = TextEditingController();
  bool _busy = false;

  @override
  void dispose() {
    _receivedBy.dispose();
    _note.dispose();
    super.dispose();
  }

  Future<void> _takePhoto() async {
    final picked = await ImagePicker().pickImage(
      source: ImageSource.camera,
      imageQuality: 70, // suficiente para leer un sello; ahorra datos moviles
      maxWidth: 1600,
    );
    if (picked != null) setState(() => _photos.add(File(picked.path)));
  }

  Future<void> _complete(String status) async {
    if (status == 'DELIVERED' && _photos.isEmpty) {
      _snack('Toma al menos una foto de soporte antes de cerrar la entrega');
      return;
    }

    setState(() => _busy = true);
    try {
      final position = await widget.location.current();

      for (final photo in _photos) {
        await widget.api.uploadProof(
          widget.delivery.id,
          photo,
          lat: position?.latitude,
          lng: position?.longitude,
          note: _note.text.trim().isEmpty ? null : _note.text.trim(),
        );
      }

      await widget.api.updateStatus(
        widget.delivery.id,
        status,
        lat: position?.latitude,
        lng: position?.longitude,
        note: _note.text.trim().isEmpty ? null : _note.text.trim(),
        failureReason: status == 'FAILED' ? _note.text.trim() : null,
        receivedBy: _receivedBy.text.trim().isEmpty ? null : _receivedBy.text.trim(),
      );

      if (!mounted) return;
      Navigator.of(context).pop(true);
    } catch (error) {
      _snack('$error'.replaceFirst('Exception: ', ''));
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  void _snack(String message) {
    ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(message)));
  }

  @override
  Widget build(BuildContext context) {
    final delivery = widget.delivery;

    return Scaffold(
      appBar: AppBar(title: Text('Parada ${delivery.sequence ?? ''}')),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          if (delivery.hasCoordinates)
            SizedBox(
              height: 180,
              child: ClipRRect(
                borderRadius: BorderRadius.circular(14),
                child: FlutterMap(
                  options: MapOptions(
                    initialCenter: LatLng(delivery.lat!, delivery.lng!),
                    initialZoom: 16,
                    interactionOptions:
                        const InteractionOptions(flags: InteractiveFlag.pinchZoom | InteractiveFlag.drag),
                  ),
                  children: [
                    // Mismos tiles de OpenStreetMap que el dashboard: $0.
                    TileLayer(
                      urlTemplate: AppConfig.tileUrl,
                      userAgentPackageName: AppConfig.userAgent,
                    ),
                    MarkerLayer(markers: [
                      Marker(
                        point: LatLng(delivery.lat!, delivery.lng!),
                        child: const Icon(Icons.location_on, color: kBrand, size: 34),
                      ),
                    ]),
                  ],
                ),
              ),
            ),
          const SizedBox(height: 16),
          Text(delivery.clientName,
              style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
          const SizedBox(height: 4),
          Text('Doc. ${delivery.documentNumber}',
              style: const TextStyle(color: kContentSecondary, fontSize: 12)),
          const SizedBox(height: 12),
          Text('${delivery.address}${delivery.locality != null ? ', ${delivery.locality}' : ''}',
              style: const TextStyle(color: kContentSecondary)),
          const SizedBox(height: 12),
          Wrap(spacing: 8, runSpacing: 8, children: [
            _Chip(label: '${delivery.weightKg.toStringAsFixed(1)} kg'),
            _Chip(label: '${delivery.units} und'),
            _Chip(label: '${delivery.items} items'),
            if (delivery.timeWindowLabel != null)
              _Chip(
                label: delivery.timeWindowLabel!,
                color: delivery.requiresAppointment ? kStatusWarning : kBrand,
              ),
          ]),
          if (delivery.comments != null) ...[
            const SizedBox(height: 16),
            Container(
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: kSurfaceRaised,
                borderRadius: BorderRadius.circular(10),
                border: Border.all(color: kBorderSubtle),
              ),
              child: Text(delivery.comments!,
                  style: const TextStyle(fontSize: 12, color: kContentSecondary)),
            ),
          ],
          const SizedBox(height: 24),
          const Text('Evidencia de entrega',
              style: TextStyle(fontWeight: FontWeight.bold, fontSize: 14)),
          const SizedBox(height: 8),
          SizedBox(
            height: 92,
            child: ListView(
              scrollDirection: Axis.horizontal,
              children: [
                ..._photos.map((photo) => Padding(
                      padding: const EdgeInsets.only(right: 8),
                      child: ClipRRect(
                        borderRadius: BorderRadius.circular(10),
                        child: Image.file(photo, width: 92, height: 92, fit: BoxFit.cover),
                      ),
                    )),
                InkWell(
                  onTap: _takePhoto,
                  child: Container(
                    width: 92,
                    height: 92,
                    decoration: BoxDecoration(
                      borderRadius: BorderRadius.circular(10),
                      border: Border.all(color: kBorderSubtle),
                    ),
                    child: const Icon(Icons.photo_camera_outlined, color: kContentSecondary),
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(height: 16),
          TextField(
            controller: _receivedBy,
            decoration: const InputDecoration(
              labelText: 'Recibido por',
              border: OutlineInputBorder(),
            ),
          ),
          const SizedBox(height: 12),
          TextField(
            controller: _note,
            maxLines: 2,
            decoration: const InputDecoration(
              labelText: 'Observaciones / novedad',
              border: OutlineInputBorder(),
            ),
          ),
          const SizedBox(height: 24),
          FilledButton.icon(
            onPressed: _busy ? null : () => _complete('DELIVERED'),
            icon: const Icon(Icons.check_circle_outline),
            label: Text(_busy ? 'Enviando…' : 'Marcar como entregada'),
          ),
          const SizedBox(height: 10),
          OutlinedButton.icon(
            onPressed: _busy ? null : () => _complete('FAILED'),
            style: OutlinedButton.styleFrom(
              foregroundColor: kStatusFailed,
              minimumSize: const Size.fromHeight(48),
            ),
            icon: const Icon(Icons.error_outline),
            label: const Text('Registrar novedad'),
          ),
        ],
      ),
    );
  }
}

class _Chip extends StatelessWidget {
  const _Chip({required this.label, this.color});

  final String label;
  final Color? color;

  @override
  Widget build(BuildContext context) => Container(
        padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
        decoration: BoxDecoration(
          color: (color ?? kContentSecondary).withValues(alpha: 0.12),
          borderRadius: BorderRadius.circular(999),
        ),
        child: Text(label,
            style: TextStyle(fontSize: 11, color: color ?? kContentSecondary)),
      );
}
