// ignore_for_file: unused_element
import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import '../../../core/colors.dart';

// TODO: replace with provider data
const _mockDisplayName = 'René Villanueva';
const _mockInitials    = 'RV';
const _mockTitle       = 'Product Designer';
const _mockCompany     = 'Salo Labs';
const _mockViewCount   = 143;

// Displays the user's avatar, display name, title, and view count
// at the top of the profile card.
class AvatarSection extends StatelessWidget {
  final String displayName;
  final String initials;
  final String title;
  final String company;
  final int    viewCount;

  const AvatarSection({
    required this.displayName,
    required this.initials,
    required this.title,
    required this.company,
    required this.viewCount,
  });

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
                  initials,
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
            displayName,
            style: GoogleFonts.plusJakartaSans(
              fontSize:   18,
              fontWeight: FontWeight.w700,
              color:      AppColors.cardText,
              height:     1.1,
            ),
          ),
          const SizedBox(height: 2),
          Text(
            '$title · $company',
            style: GoogleFonts.plusJakartaSans(
              fontSize: 13,
              color:    AppColors.cardMuted,
            ),
          ),
          const SizedBox(height: 4),
          Text(
            '$viewCount views',
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
