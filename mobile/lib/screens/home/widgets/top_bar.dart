import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import '../../../core/colors.dart';

// App bar for the home screen: hamburger menu on the left, slug handle
// in the centre, and a preview (eye) icon on the right.
// _HamburgerIcon is kept here as it is only used by TopBar.
class TopBar extends StatelessWidget {
  final String       slug;
  final VoidCallback onEyeTap;

  const TopBar({required this.slug, required this.onEyeTap});

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      height: 50,
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 16),
        child: Row(
          children: [
            const _HamburgerIcon(),
            const Spacer(),
            Text(
              '@$slug',
              style: GoogleFonts.plusJakartaSans(
                fontSize:      13,
                fontWeight:    FontWeight.w500,
                color:         AppColors.muted,
                letterSpacing: 0.2,
              ),
            ),
            const Spacer(),
            GestureDetector(
              onTap:    onEyeTap,
              behavior: HitTestBehavior.opaque,
              child: const SizedBox(
                width:  36,
                height: 36,
                child: Center(
                  child: Icon(
                    Icons.remove_red_eye_outlined,
                    color: AppColors.muted,
                    size:  22,
                  ),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _HamburgerIcon extends StatelessWidget {
  const _HamburgerIcon();

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      width:  36,
      height: 36,
      child: Column(
        mainAxisAlignment:  MainAxisAlignment.center,
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Container(width: 22, height: 1.5, color: AppColors.text),
          const SizedBox(height: 5),
          Container(width: 16, height: 1.5, color: AppColors.muted),
        ],
      ),
    );
  }
}
