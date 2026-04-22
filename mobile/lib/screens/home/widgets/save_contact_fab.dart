import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import '../../../core/colors.dart';

// Full-width "Save Contact" button shown at the bottom of the screen
// during preview mode so the owner can see what recipients will see.
class SaveContactFab extends StatelessWidget {
  const SaveContactFab();

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 20),
      child: Container(
        height: 52,
        decoration: BoxDecoration(
          color:        AppColors.cardText,
          borderRadius: BorderRadius.circular(14),
          boxShadow: const [
            BoxShadow(
              color:      Color(0x3A1A1814),
              blurRadius: 16,
              offset:     Offset(0, 4),
            ),
          ],
        ),
        child: Row(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Icon(Icons.person_add_outlined, color: AppColors.card, size: 18),
            const SizedBox(width: 8),
            Text(
              'Save Contact',
              style: GoogleFonts.plusJakartaSans(
                fontSize:   15,
                fontWeight: FontWeight.w600,
                color:      AppColors.card,
              ),
            ),
          ],
        ),
      ),
    );
  }
}
