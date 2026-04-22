import 'package:flutter/material.dart';
import '../screens/auth/login_screen.dart';
import '../screens/auth/register_screen.dart';
import '../screens/home/home_screen.dart';
import '../screens/home/qr_screen.dart';
import '../screens/profile/profile_edit_screen.dart';

class AppRouter {
  static const String login = '/';
  static const String register = '/register';
  static const String home = '/home';
  static const String profilePreview = '/profile-preview';
  static const String qr = '/qr';
  static const String profileEdit = '/profile-edit';

  static final routes = <String, WidgetBuilder>{
    login: (_) => const LoginScreen(),
    register: (_) => const RegisterScreen(),
    home: (_) => const HomeScreen(),
    qr: (_) => const QrScreen(),
    profileEdit: (_) => const ProfileEditScreen(),
  };
}
