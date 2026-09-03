import 'package:flutter/material.dart';

/// Mismos tokens que el dashboard web (`apps/web/src/styles/tokens.css`), para
/// que conductor y despachador vean el mismo producto.
const kSurfaceBase = Color(0xFF0B1017);
const kSurfaceRaised = Color(0xFF121A24);
const kBorderSubtle = Color(0xFF1F2B3A);
const kContentPrimary = Color(0xFFE8EEF6);
const kContentSecondary = Color(0xFF9FB0C3);
const kBrand = Color(0xFF2DD4BF);
const kStatusDelivered = Color(0xFF22C55E);
const kStatusFailed = Color(0xFFEF4444);
const kStatusWarning = Color(0xFFF59E0B);

ThemeData buildDriverTheme() {
  final base = ThemeData.dark(useMaterial3: true);
  return base.copyWith(
    scaffoldBackgroundColor: kSurfaceBase,
    colorScheme: base.colorScheme.copyWith(
      primary: kBrand,
      surface: kSurfaceRaised,
      error: kStatusFailed,
    ),
    appBarTheme: const AppBarTheme(
      backgroundColor: kSurfaceRaised,
      surfaceTintColor: Colors.transparent,
      elevation: 0,
    ),
    cardTheme: CardTheme(
      color: kSurfaceRaised,
      elevation: 0,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(14),
        side: const BorderSide(color: kBorderSubtle),
      ),
    ),
    filledButtonTheme: FilledButtonThemeData(
      style: FilledButton.styleFrom(
        backgroundColor: kBrand,
        foregroundColor: kSurfaceBase,
        minimumSize: const Size.fromHeight(52),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
      ),
    ),
  );
}
