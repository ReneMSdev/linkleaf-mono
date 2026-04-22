import 'package:flutter/material.dart';
import '../../../core/colors.dart';

// Floating circular edit button shown in the bottom-right corner
// of the home screen when not in preview mode.
class EditFab extends StatelessWidget {
  final VoidCallback onTap;
  const EditFab({required this.onTap});

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        width:  52,
        height: 52,
        decoration: BoxDecoration(
          color:  AppColors.accent,
          shape:  BoxShape.circle,
          boxShadow: const [
            BoxShadow(
              color:      Color(0x3A1A1814),
              blurRadius: 12,
              offset:     Offset(0, 4),
            ),
          ],
        ),
        child: const Icon(Icons.edit_outlined, color: Colors.white, size: 22),
      ),
    );
  }
}
