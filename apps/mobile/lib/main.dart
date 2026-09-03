import 'package:flutter/material.dart';
import 'services/api_client.dart';
import 'services/location_service.dart';
import 'screens/login_screen.dart';
import 'theme.dart';

void main() {
  runApp(const CgCargaDriverApp());
}

class CgCargaDriverApp extends StatelessWidget {
  const CgCargaDriverApp({super.key});

  @override
  Widget build(BuildContext context) {
    final api = ApiClient();
    return MaterialApp(
      title: 'CG CARGA Conductor',
      debugShowCheckedModeBanner: false,
      theme: buildDriverTheme(),
      home: LoginScreen(api: api, location: LocationService(api)),
    );
  }
}
