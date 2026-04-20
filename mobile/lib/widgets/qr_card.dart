import 'package:flutter/material.dart';

class QrCard extends StatelessWidget {
  const QrCard({super.key});

  @override
  Widget build(BuildContext context) {
    return const Card(
      child: Padding(
        padding: EdgeInsets.all(16),
        child: Icon(Icons.qr_code, size: 128),
      ),
    );
  }
}
