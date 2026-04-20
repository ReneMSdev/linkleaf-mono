import 'package:flutter/material.dart';
import '../../core/router.dart';

class HomeScreen extends StatelessWidget {
  const HomeScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Home')),
      body: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            ElevatedButton(
              onPressed: () => Navigator.pushNamed(context, AppRouter.profilePreview),
              child: const Text('Preview Profile'),
            ),
            ElevatedButton(
              onPressed: () => Navigator.pushNamed(context, AppRouter.qr),
              child: const Text('My QR Code'),
            ),
            ElevatedButton(
              onPressed: () => Navigator.pushNamed(context, AppRouter.profileEdit),
              child: const Text('Edit Profile'),
            ),
          ],
        ),
      ),
    );
  }
}
