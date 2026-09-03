import 'package:flutter/material.dart';
import '../services/api_client.dart';
import '../services/location_service.dart';
import 'routes_screen.dart';

class LoginScreen extends StatefulWidget {
  const LoginScreen({super.key, required this.api, required this.location});

  final ApiClient api;
  final LocationService location;

  @override
  State<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen> {
  final _document = TextEditingController();
  final _phone = TextEditingController();
  bool _busy = false;
  String? _error;

  @override
  void dispose() {
    _document.dispose();
    _phone.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    setState(() {
      _busy = true;
      _error = null;
    });
    try {
      await widget.api.login(_document.text.trim(), _phone.text.trim());
      // El permiso de ubicacion se pide aqui, con el contexto de la jornada
      // recien iniciada, no de golpe al abrir la app.
      await widget.location.ensurePermission();
      if (!mounted) return;
      Navigator.of(context).pushReplacement(
        MaterialPageRoute(
          builder: (_) => RoutesScreen(api: widget.api, location: widget.location),
        ),
      );
    } catch (error) {
      setState(() => _error = error.toString().replaceFirst('Exception: ', ''));
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              const Text('CG CARGA',
                  style: TextStyle(fontSize: 28, fontWeight: FontWeight.w900, letterSpacing: 2)),
              const SizedBox(height: 4),
              const Text('App de conductores', style: TextStyle(color: Color(0xFF9FB0C3))),
              const SizedBox(height: 40),
              TextField(
                controller: _document,
                keyboardType: TextInputType.number,
                decoration: const InputDecoration(
                  labelText: 'Numero de cedula',
                  border: OutlineInputBorder(),
                ),
              ),
              const SizedBox(height: 14),
              TextField(
                controller: _phone,
                keyboardType: TextInputType.phone,
                decoration: const InputDecoration(
                  labelText: 'Celular registrado',
                  border: OutlineInputBorder(),
                ),
              ),
              if (_error != null) ...[
                const SizedBox(height: 14),
                Text(_error!, style: const TextStyle(color: Color(0xFFEF4444), fontSize: 13)),
              ],
              const SizedBox(height: 28),
              FilledButton(
                onPressed: _busy ? null : _submit,
                child: _busy
                    ? const SizedBox(
                        height: 20, width: 20, child: CircularProgressIndicator(strokeWidth: 2))
                    : const Text('Iniciar jornada'),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
