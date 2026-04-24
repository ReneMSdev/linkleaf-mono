import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import '../../../core/colors.dart';

// Visible only in debug builds. Tap to toggle free ↔ premium tier so you
// can inspect both UI states without touching provider data.
class DevTierFab extends StatelessWidget {
  final bool isPremium;
  final VoidCallback onToggle;

  const DevTierFab({required this.isPremium, required this.onToggle});

  @override
  Widget build(BuildContext context) {
    if (!kDebugMode) return const SizedBox.shrink();
    return GestureDetector(
      onTap: onToggle,
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
        decoration: BoxDecoration(
          color: isPremium ? AppColors.accent : AppColors.surface,
          borderRadius: BorderRadius.circular(20),
          border: Border.all(
            color: isPremium ? AppColors.accent : AppColors.border,
          ),
          boxShadow: const [
            BoxShadow(
              color: Color(0x33000000),
              blurRadius: 8,
              offset: Offset(0, 2),
            ),
          ],
        ),
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(
              isPremium ? Icons.workspace_premium_outlined : Icons.lock_outline,
              size: 13,
              color: isPremium ? AppColors.bg : AppColors.muted,
            ),
            const SizedBox(width: 5),
            Text(
              isPremium ? 'PRO' : 'FREE',
              style: GoogleFonts.plusJakartaSans(
                fontSize: 11,
                fontWeight: FontWeight.w700,
                letterSpacing: 0.5,
                color: isPremium ? AppColors.bg : AppColors.muted,
              ),
            ),
          ],
        ),
      ),
    );
  }
}
