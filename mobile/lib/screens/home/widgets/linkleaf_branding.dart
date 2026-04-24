import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import '../../../core/colors.dart';

class LinkLeafBranding extends StatelessWidget {
  const LinkLeafBranding();

  @override
  Widget build(BuildContext context) {
    return Row(
      mainAxisAlignment: MainAxisAlignment.center,
      children: [
        _LeafIcon(),
        const SizedBox(width: 5),
        Text(
          'LinkLeaf',
          style: GoogleFonts.plusJakartaSans(
            fontSize: 12,
            fontWeight: FontWeight.w600,
            color: AppColors.cardText,
          ),
        ),
      ],
    );
  }
}

class _LeafIcon extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return Container(
      width: 16,
      height: 16,
      decoration: BoxDecoration(
        color: AppColors.cardBorder,
        borderRadius: BorderRadius.circular(4),
      ),
      child: const Icon(
        Icons.eco_outlined,
        size: 11,
        color: AppColors.cardMuted,
      ),
    );
  }
}
