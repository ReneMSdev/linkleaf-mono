import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';

// TODO: replace with provider data
const _mockInitials  = 'RV';
const _mockAvatarUrl = null; // placeholder for future image support

class AvatarImage extends StatelessWidget {
  final String  initials;
  final String? avatarUrl;

  const AvatarImage({
    this.initials  = _mockInitials,
    this.avatarUrl = _mockAvatarUrl,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
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
    );
  }
}
