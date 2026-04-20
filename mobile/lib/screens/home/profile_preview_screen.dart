import 'package:flutter/material.dart';

class ProfilePreviewScreen extends StatelessWidget {
  const ProfilePreviewScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Profile Preview')),
      body: const Center(child: Text('Profile Preview Screen')),
    );
  }
}
