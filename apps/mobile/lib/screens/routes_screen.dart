import 'package:flutter/material.dart';
import '../models/delivery.dart';
import '../services/api_client.dart';
import '../services/location_service.dart';
import '../theme.dart';
import 'delivery_screen.dart';

class RoutesScreen extends StatefulWidget {
  const RoutesScreen({super.key, required this.api, required this.location});

  final ApiClient api;
  final LocationService location;

  @override
  State<RoutesScreen> createState() => _RoutesScreenState();
}

class _RoutesScreenState extends State<RoutesScreen> {
  late Future<List<DriverRoute>> _future;

  @override
  void initState() {
    super.initState();
    _future = widget.api.fetchRoutes(DateTime.now());
  }

  Future<void> _reload() async {
    setState(() => _future = widget.api.fetchRoutes(DateTime.now()));
    await _future;
  }

  Color _colorFor(String hex) =>
      Color(int.parse(hex.replaceFirst('#', 'FF'), radix: 16));

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Mis rutas de hoy'),
        actions: [IconButton(onPressed: _reload, icon: const Icon(Icons.refresh))],
      ),
      body: FutureBuilder<List<DriverRoute>>(
        future: _future,
        builder: (context, snapshot) {
          if (snapshot.connectionState == ConnectionState.waiting) {
            return const Center(child: CircularProgressIndicator());
          }
          if (snapshot.hasError) {
            return _ErrorState(message: '${snapshot.error}', onRetry: _reload);
          }

          final routes = snapshot.data ?? [];
          if (routes.isEmpty) {
            return const Center(
              child: Text('No tienes rutas asignadas para hoy',
                  style: TextStyle(color: kContentSecondary)),
            );
          }

          return RefreshIndicator(
            onRefresh: _reload,
            child: ListView.builder(
              padding: const EdgeInsets.all(16),
              itemCount: routes.length,
              itemBuilder: (context, index) {
                final route = routes[index];
                final color = _colorFor(route.color);

                return Card(
                  margin: const EdgeInsets.only(bottom: 16),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Padding(
                        padding: const EdgeInsets.fromLTRB(16, 16, 16, 8),
                        child: Row(
                          children: [
                            Container(width: 10, height: 10,
                                decoration: BoxDecoration(color: color, shape: BoxShape.circle)),
                            const SizedBox(width: 10),
                            Text('Ruta ${route.code}',
                                style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
                            const Spacer(),
                            Text('${route.delivered}/${route.deliveries.length}',
                                style: const TextStyle(color: kContentSecondary)),
                          ],
                        ),
                      ),
                      LinearProgressIndicator(
                        value: route.deliveries.isEmpty
                            ? 0
                            : route.delivered / route.deliveries.length,
                        backgroundColor: kBorderSubtle,
                        color: color,
                        minHeight: 3,
                      ),
                      ...route.deliveries.map(
                        (delivery) => _DeliveryTile(
                          delivery: delivery,
                          color: color,
                          onTap: () async {
                            widget.location.startTracking(route.id);
                            await Navigator.of(context).push(
                              MaterialPageRoute(
                                builder: (_) => DeliveryScreen(
                                  api: widget.api,
                                  location: widget.location,
                                  delivery: delivery,
                                ),
                              ),
                            );
                            await _reload();
                          },
                        ),
                      ),
                    ],
                  ),
                );
              },
            ),
          );
        },
      ),
    );
  }
}

class _DeliveryTile extends StatelessWidget {
  const _DeliveryTile({required this.delivery, required this.color, required this.onTap});

  final Delivery delivery;
  final Color color;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    final done = delivery.status == 'DELIVERED';
    final failed = delivery.status == 'FAILED';

    return ListTile(
      onTap: onTap,
      leading: CircleAvatar(
        radius: 14,
        backgroundColor: done ? kStatusDelivered : (failed ? kStatusFailed : color),
        child: done
            ? const Icon(Icons.check, size: 16, color: kSurfaceBase)
            : Text('${delivery.sequence ?? '-'}',
                style: const TextStyle(fontSize: 12, fontWeight: FontWeight.bold, color: kSurfaceBase)),
      ),
      title: Text(delivery.clientName,
          maxLines: 1, overflow: TextOverflow.ellipsis,
          style: const TextStyle(fontSize: 14, fontWeight: FontWeight.w600)),
      subtitle: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text('${delivery.address}${delivery.locality != null ? ', ${delivery.locality}' : ''}',
              maxLines: 1, overflow: TextOverflow.ellipsis,
              style: const TextStyle(fontSize: 12, color: kContentSecondary)),
          if (delivery.timeWindowLabel != null)
            Text(delivery.timeWindowLabel!,
                style: TextStyle(
                    fontSize: 11,
                    color: delivery.requiresAppointment ? kStatusWarning : kBrand)),
        ],
      ),
      trailing: const Icon(Icons.chevron_right, size: 18, color: kContentSecondary),
    );
  }
}

class _ErrorState extends StatelessWidget {
  const _ErrorState({required this.message, required this.onRetry});

  final String message;
  final VoidCallback onRetry;

  @override
  Widget build(BuildContext context) => Center(
        child: Padding(
          padding: const EdgeInsets.all(32),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              Text(message, textAlign: TextAlign.center,
                  style: const TextStyle(color: kContentSecondary)),
              const SizedBox(height: 16),
              FilledButton(onPressed: onRetry, child: const Text('Reintentar')),
            ],
          ),
        ),
      );
}
