import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import '../../../core/colors.dart';

class EditTopBar extends StatelessWidget {
  final String       slug;
  final VoidCallback onContact;
  final VoidCallback onTheme;
  final VoidCallback onDone;

  const EditTopBar({
    required this.slug,
    required this.onContact,
    required this.onTheme,
    required this.onDone,
  });

  TextStyle get _buttonStyle => GoogleFonts.plusJakartaSans(
        fontSize:   13,
        fontWeight: FontWeight.w500,
        color:      AppColors.muted,
      );

  @override
  Widget build(BuildContext context) {
    return Container(
      height: 50,
      decoration: const BoxDecoration(
        color: AppColors.surface,
        border: Border(
          bottom: BorderSide(color: AppColors.border, width: 1),
        ),
      ),
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 16),
        child: Row(
          children: [
            GestureDetector(
              onTap:    onContact,
              behavior: HitTestBehavior.opaque,
              child: Text('Contact', style: _buttonStyle),
            ),
            const SizedBox(width: 16),
            GestureDetector(
              onTap:    onTheme,
              behavior: HitTestBehavior.opaque,
              child: Text('Theme', style: _buttonStyle),
            ),
            Expanded(
              child: Center(
                child: Text(
                  '@$slug',
                  style: GoogleFonts.plusJakartaSans(
                    fontSize:      13,
                    fontWeight:    FontWeight.w500,
                    color:         AppColors.muted,
                    letterSpacing: 0.2,
                  ),
                ),
              ),
            ),
            GestureDetector(
              onTap:    onDone,
              behavior: HitTestBehavior.opaque,
              child: Text(
                'Done',
                style: GoogleFonts.plusJakartaSans(
                  fontSize:   15,
                  fontWeight: FontWeight.w600,
                  color:      AppColors.cardText,
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
