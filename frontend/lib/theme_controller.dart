import 'package:flutter/material.dart';

class ThemeController {
  ThemeController._internal();
  static final ThemeController instance = ThemeController._internal();

  final ValueNotifier<ThemeMode> themeMode = ValueNotifier<ThemeMode>(ThemeMode.system);

  void setThemeMode(ThemeMode mode) {
    themeMode.value = mode;
  }
}


