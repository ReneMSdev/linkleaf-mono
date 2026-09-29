import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import '../../../core/colors.dart';

// Banner overlaid at the top of the screen during profile preview mode.
// Shows a "Previewing your public profile" message and a close button.
// _PreviewCloseButton is kept here as it is only used by PreviewBanner.
class PreviewBanner extends StatelessWidget {
  final double       topInset;
  final EdgeInsets   horizontalPadding;
  final Color        background;
  final bool         showSensitiveLine;
  final Color        onBanner;
  final Color        onBannerMuted;
  final VoidCallback onClose;

  const PreviewBanner({
    required this.topInset,
    required this.horizontalPadding,
    required this.background,
    required this.showSensitiveLine,
    required this.onBanner,
    required this.onBannerMuted,
    required this.onClose,
  });

  /// Matches this widget's vertical layout (status strip + accent row) plus
  /// a small gap so list content clears the banner.
  static double listTopInset({
    required double topInset,
    required bool   showSensitiveLine,
    double gapBelowBanner = 12,
  }) {
    const padY         = 20.0;
    const fs1          = 12.0;
    const h1           = 1.2;
    const fs2          = 10.0;
    const h2           = 1.2;
    const betweenLines = 4.0;
    var textCol = fs1 * h1;
    if (showSensitiveLine) textCol += betweenLines + fs2 * h2;
    const btn  = 44.0;
    final rowH = textCol > btn ? textCol : btn;
    return topInset + padY + rowH + gapBelowBanner;
  }

  @override
  Widget build(BuildContext context) {
    return Column(
      mainAxisSize:     MainAxisSize.min,
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        if (topInset > 0)
          SizedBox(
            height: topInset,
            child: const ColoredBox(color: AppColors.card),
          ),
        ColoredBox(
          color: background,
          child: Padding(
            padding: EdgeInsets.fromLTRB(
              horizontalPadding.left + 16,
              10,
              horizontalPadding.right + 8,
              10,
            ),
            child: Row(
              crossAxisAlignment: CrossAxisAlignment.center,
              children: [
                Expanded(
                  child: Column(
                    mainAxisSize:       MainAxisSize.min,
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        'Previewing your public profile',
                        textAlign: TextAlign.left,
                        style: GoogleFonts.plusJakartaSans(
                          fontSize:   12,
                          fontWeight: FontWeight.w500,
                          color:      onBanner,
                          height:     1.2,
                        ),
                      ),
                      if (showSensitiveLine) ...[
                        const SizedBox(height: 4),
                        Text(
                          'Includes contact info',
                          textAlign: TextAlign.left,
                          style: GoogleFonts.plusJakartaSans(
                            fontSize: 10,
                            color:    onBannerMuted,
                            height:   1.2,
                          ),
                        ),
                      ],
                    ],
                  ),
                ),
                _PreviewCloseButton(onTap: onClose),
              ],
            ),
          ),
        ),
      ],
    );
  }
}

class _PreviewCloseButton extends StatelessWidget {
  final VoidCallback onTap;
  const _PreviewCloseButton({required this.onTap});

  @override
  Widget build(BuildContext context) {
    return Material(
      color: Colors.transparent,
      child: InkWell(
        customBorder: const CircleBorder(),
        onTap: onTap,
        child: Ink(
          width:  44,
          height: 44,
          decoration: const BoxDecoration(
            shape: BoxShape.circle,
            color: Color(0x4D000000),
          ),
          child: const Icon(Icons.close, color: Colors.white, size: 22),
        ),
      ),
    );
  }
}
