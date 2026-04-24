import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import '../../../core/colors.dart';

// TODO: replace with provider data
const _mockDisplayName = 'René Villanueva';
const _mockTitle = 'Product Designer';
const _mockCompany = 'Salo Labs';
const _mockBio = 'Building thoughtful digital products. Based in Mexico City.';
const _mockViewCount = 143;

class ProfileInfo extends StatelessWidget {
  final String displayName;
  final String title;
  final String company;
  final String? bio;
  final int viewCount;

  const ProfileInfo({
    this.displayName = _mockDisplayName,
    this.title = _mockTitle,
    this.company = _mockCompany,
    this.bio = _mockBio,
    this.viewCount = _mockViewCount,
  });

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        const SizedBox(height: 8),
        Text(
          displayName,
          style: GoogleFonts.plusJakartaSans(
            fontSize: 18,
            fontWeight: FontWeight.w700,
            color: AppColors.cardText,
            height: 1.1,
          ),
        ),
        const SizedBox(height: 2),
        Text(
          '$title · $company',
          style: GoogleFonts.plusJakartaSans(
            fontSize: 13,
            color: AppColors.cardMuted,
          ),
        ),
        if (bio != null) ...[
          const SizedBox(height: 2),
          Text(
            bio!,
            style: GoogleFonts.plusJakartaSans(
              fontSize: 13,
              color: AppColors.cardMuted,
            ),
          ),
        ],
        const SizedBox(height: 4),
        Text(
          '$viewCount views',
          style: GoogleFonts.plusJakartaSans(
            fontSize: 11,
            color: const Color(0x998C8070),
          ),
        ),
      ],
    );
  }
}
