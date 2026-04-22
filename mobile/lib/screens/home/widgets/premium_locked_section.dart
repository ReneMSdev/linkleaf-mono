import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import '../../../core/colors.dart';

// Placeholder row for a feature gated behind a premium subscription.
// Displays a lock icon, a label, and a "· Premium" badge.
class PremiumLockedSection extends StatelessWidget {
  final String label;
  const PremiumLockedSection({required this.label});

  @override
  Widget build(BuildContext context) {
    return Container(
      height: 68,
      decoration: BoxDecoration(
        color:        AppColors.cardSub,
        border:       Border.all(color: AppColors.cardBorder),
        borderRadius: BorderRadius.circular(12),
      ),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          const Icon(Icons.lock_outline, size: 15, color: AppColors.cardBorder),
          const SizedBox(width: 8),
          Text(
            label,
            style: GoogleFonts.plusJakartaSans(
              fontSize: 13,
              color:    AppColors.cardBorder,
            ),
          ),
          Text(
            ' · Premium',
            style: GoogleFonts.plusJakartaSans(
              fontSize: 12,
              color:    const Color(0xFFD0C8BC),
            ),
          ),
        ],
      ),
    );
  }
}
