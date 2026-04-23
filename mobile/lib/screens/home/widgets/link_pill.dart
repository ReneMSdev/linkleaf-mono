// ignore_for_file: unused_element
import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import '../../../core/colors.dart';
import '../../../models/link.dart';

// TODO: replace with provider data
// Example link shape — not used by the widget itself.
const _mockLink = Link(id: '1', title: 'Portfolio', url: 'https://portfolio.example.com');

// A tappable pill representing a single profile link (title + chevron).
// Renders as non-interactive when linkPreviewLocked is true.
class LinkPill extends StatelessWidget {
  final Link link;
  final bool linkPreviewLocked;

  const LinkPill({required this.link, this.linkPreviewLocked = false});

  Color get _iconBg {
    switch (link.title.toLowerCase()) {
      case 'portfolio': return const Color(0xFFFF6B35);
      case 'github':    return const Color(0xFF1A1814);
      case 'linkedin':  return const Color(0xFF0A66C2);
      case 'dribbble':  return const Color(0xFFEA4C89);
      default:          return AppColors.muted;
    }
  }

  @override
  Widget build(BuildContext context) {
    final content = Container(
      decoration: BoxDecoration(
        color:        AppColors.card,
        border:       Border.all(color: AppColors.cardBorder),
        borderRadius: BorderRadius.circular(12),
        boxShadow: const [
          BoxShadow(
            color:      Color(0x0F1A1814),
            blurRadius: 3,
            offset:     Offset(0, 1),
          ),
        ],
      ),
      child: Material(
        color: Colors.transparent,
        child: InkWell(
          borderRadius: BorderRadius.circular(12),
          onTap: linkPreviewLocked ? null : () {},
          child: Padding(
            padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 11),
            child: Row(
              children: [
                Container(
                  width:  24,
                  height: 24,
                  decoration: BoxDecoration(
                    color:        _iconBg,
                    borderRadius: BorderRadius.circular(6),
                  ),
                  child: Center(
                    child: Container(
                      width:  10,
                      height: 10,
                      decoration: BoxDecoration(
                        color:        const Color(0xE5FFFFFF),
                        borderRadius: BorderRadius.circular(2),
                      ),
                    ),
                  ),
                ),
                const SizedBox(width: 10),
                Expanded(
                  child: Text(
                    link.title,
                    style: GoogleFonts.plusJakartaSans(
                      fontSize:   14,
                      fontWeight: FontWeight.w500,
                      color:      AppColors.cardText,
                    ),
                  ),
                ),
                const Icon(
                  Icons.chevron_right,
                  size:  16,
                  color: Color(0x4D1A1814),
                ),
              ],
            ),
          ),
        ),
      ),
    );
    if (!linkPreviewLocked) return content;
    return IgnorePointer(child: content);
  }
}
