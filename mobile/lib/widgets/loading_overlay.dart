import 'package:flutter/material.dart';

class LoadingOverlay extends StatelessWidget {
  final Widget child;
  final bool isLoading;

  const LoadingOverlay({super.key, required this.child, this.isLoading = false});

  @override
  Widget build(BuildContext context) {
    return Stack(
      children: [
        child,
        if (isLoading) const Center(child: CircularProgressIndicator()),
      ],
    );
  }
}
