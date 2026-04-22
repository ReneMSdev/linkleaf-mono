import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import '../../../core/colors.dart';

// Displays the user's avatar, display name, title, and view count
// at the top of the profile card.
class AvatarSection extends StatelessWidget {
  const AvatarSection();

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.fromLTRB(0, 4, 0, 14),
      child: Column(
        children: [
          Container(
            width:  68,
            height: 68,
            decoration: const BoxDecoration(
              shape:    BoxShape.circle,
              gradient: LinearGradient(
                begin:  Alignment.topLeft,
                end:    Alignment.bottomRight,
                colors: [Color(0x55C9B99A), Color(0x22C9B99A)],
              ),
            ),
            padding: const EdgeInsets.all(2),
            child: Container(
              decoration: const BoxDecoration(
                shape: BoxShape.circle,
                color: Color(0xFFD8CFC4),
              ),
              child: Center(
                child: Text(
                  'RV',
                  style: GoogleFonts.plusJakartaSans(
                    fontSize:   22,
                    fontWeight: FontWeight.w700,
                    color:      const Color(0xFF8C7E6E),
                  ),
                ),
              ),
            ),
          ),
          const SizedBox(height: 8),
          Text(
            'René Villanueva',
            style: GoogleFonts.plusJakartaSans(
              fontSize:   18,
              fontWeight: FontWeight.w700,
              color:      AppColors.cardText,
              height:     1.1,
            ),
          ),
          const SizedBox(height: 2),
          Text(
            'Product Designer · Salo Labs',
            style: GoogleFonts.plusJakartaSans(
              fontSize: 13,
              color:    AppColors.cardMuted,
            ),
          ),
          const SizedBox(height: 4),
          Text(
            '143 views',
            style: GoogleFonts.plusJakartaSans(
              fontSize: 11,
              color:    const Color(0x998C8070),
            ),
          ),
        ],
      ),
    );
  }
}
