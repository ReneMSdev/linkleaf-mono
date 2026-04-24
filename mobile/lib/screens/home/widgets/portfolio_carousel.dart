import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import '../../../core/colors.dart';

class PortfolioCarousel extends StatefulWidget {
  final int imageCount;
  const PortfolioCarousel({this.imageCount = 4});

  @override
  State<PortfolioCarousel> createState() => _PortfolioCarouselState();
}

class _PortfolioCarouselState extends State<PortfolioCarousel> {
  int _active = 0;

  void _prev() {
    if (_active > 0) setState(() => _active--);
  }

  void _next() {
    if (_active < widget.imageCount - 1) setState(() => _active++);
  }

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Padding(
          padding: const EdgeInsets.fromLTRB(20, 0, 20, 10),
          child: Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text(
                'PORTFOLIO',
                style: GoogleFonts.plusJakartaSans(
                  fontSize: 11,
                  fontWeight: FontWeight.w600,
                  letterSpacing: 1,
                  color: AppColors.cardMuted,
                ),
              ),
              Text(
                '${_active + 1} / ${widget.imageCount}',
                style: GoogleFonts.plusJakartaSans(
                  fontSize: 11,
                  color: AppColors.cardMuted,
                ),
              ),
            ],
          ),
        ),
        AspectRatio(
          aspectRatio: 3 / 4,
          child: Stack(
            fit: StackFit.expand,
            children: [
              Container(
                color: AppColors.cardSub,
                child: Column(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    const Icon(
                      Icons.image_outlined,
                      size: 28,
                      color: AppColors.cardMuted,
                    ),
                    const SizedBox(height: 6),
                    Text(
                      'Image ${_active + 1}',
                      style: GoogleFonts.plusJakartaSans(
                        fontSize: 12,
                        color: AppColors.cardText,
                      ),
                    ),
                  ],
                ),
              ),
              Positioned.fill(
                child: Row(
                  children: [
                    Expanded(
                      child: GestureDetector(
                        onTap: _prev,
                        behavior: HitTestBehavior.translucent,
                      ),
                    ),
                    Expanded(
                      child: GestureDetector(
                        onTap: _next,
                        behavior: HitTestBehavior.translucent,
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ),
        ),
        Padding(
          padding: const EdgeInsets.only(top: 10, bottom: 4),
          child: Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: List.generate(widget.imageCount, (i) {
              return GestureDetector(
                onTap: () => setState(() => _active = i),
                child: AnimatedContainer(
                  duration: const Duration(milliseconds: 200),
                  margin: const EdgeInsets.symmetric(horizontal: 2.5),
                  width: i == _active ? 18 : 5,
                  height: 5,
                  decoration: BoxDecoration(
                    color: i == _active ? AppColors.cardText : AppColors.cardBorder,
                    borderRadius: BorderRadius.circular(3),
                  ),
                ),
              );
            }),
          ),
        ),
      ],
    );
  }
}
