import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import '../../../core/colors.dart';

// Persistent bottom navigation bar with Home, Profiles, and Themes tabs.
class _NavTab {
  final String   label;
  final IconData icon;
  final IconData activeIcon;
  const _NavTab(this.label, this.icon, this.activeIcon);
}

const _navTabs = [
  _NavTab('Home',     Icons.home_outlined,    Icons.home),
  _NavTab('Profiles', Icons.person_outline,   Icons.person),
  _NavTab('Themes',   Icons.palette_outlined, Icons.palette),
];

class BottomNav extends StatelessWidget {
  final int              currentIndex;
  final double           bottomPad;
  final ValueChanged<int> onTap;

  const BottomNav({
    required this.currentIndex,
    required this.bottomPad,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      height: 62 + bottomPad,
      decoration: const BoxDecoration(
        color:  AppColors.surface,
        border: Border(top: BorderSide(color: AppColors.border)),
      ),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceAround,
        children: List.generate(_navTabs.length, (i) {
          final tab    = _navTabs[i];
          final active = i == currentIndex;
          final color  = active ? AppColors.accent : AppColors.muted;
          return GestureDetector(
            onTap:    () => onTap(i),
            behavior: HitTestBehavior.opaque,
            child: SizedBox(
              width: 72,
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Icon(
                    active ? tab.activeIcon : tab.icon,
                    size:  20,
                    color: color,
                  ),
                  const SizedBox(height: 3),
                  Text(
                    tab.label,
                    style: GoogleFonts.plusJakartaSans(
                      fontSize:      10,
                      fontWeight:    active ? FontWeight.w600 : FontWeight.w400,
                      color:         color,
                      letterSpacing: 0.2,
                    ),
                  ),
                ],
              ),
            ),
          );
        }),
      ),
    );
  }
}
