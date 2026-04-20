import 'package:flutter/material.dart';
import '../../core/router.dart';

class LoginScreen extends StatelessWidget {
  const LoginScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('LinkLeaf')),
      body: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Text('Login', style: TextStyle(fontSize: 24)),
            const SizedBox(height: 24),
            ElevatedButton(
              onPressed: () => Navigator.pushNamed(context, AppRouter.home),
              child: const Text('Sign In'),
            ),
            TextButton(
              onPressed: () => Navigator.pushNamed(context, AppRouter.register),
              child: const Text('Create Account'),
            ),
          ],
        ),
      ),
    );
  }
}
