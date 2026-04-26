import 'dart:math' as math;
import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import '../../../core/colors.dart';

// TODO: replace with provider data
const _mockInitials  = 'RV';
const _mockAvatarUrl = null; // placeholder for future image support

class AvatarImage extends StatelessWidget {
  final String  initials;
  final String? avatarUrl;
  final bool    editMode;

  const AvatarImage({
    this.initials  = _mockInitials,
    this.avatarUrl = _mockAvatarUrl,
    this.editMode  = false,
  });

  @override
  Widget build(BuildContext context) {
    if (!editMode) return _buildLive();

    return GestureDetector(
      onTap: () {},
      child: SizedBox(
        width:  68,
        height: 68,
        child: Stack(
          children: [
            Positioned.fill(
              child: CustomPaint(
                painter: _DashedCirclePainter(color: AppColors.accent),
              ),
            ),
            Positioned.fill(
              child: Padding(
                padding: const EdgeInsets.all(2),
                child: _innerCircle(),
              ),
            ),
            Positioned(
              right:  0,
              bottom: 0,
              child: Container(
                width:  24,
                height: 24,
                decoration: BoxDecoration(
                  color:  AppColors.cardText,
                  shape:  BoxShape.circle,
                  border: Border.all(color: AppColors.card, width: 1.5),
                ),
                child: const Icon(
                  Icons.camera_alt,
                  size:  12,
                  color: Colors.white,
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildLive() {
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
      child: _innerCircle(),
    );
  }

  Widget _innerCircle() {
    return Container(
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
    );
  }
}

// ── Dashed circle border ───────────────────────────────────────────────────

class _DashedCirclePainter extends CustomPainter {
  final Color color;

  const _DashedCirclePainter({required this.color});

  static const _strokeWidth = 1.5;
  static const _dashLength  = 5.0;
  static const _gapLength   = 4.0;

  @override
  void paint(Canvas canvas, Size size) {
    final paint = Paint()
      ..color       = color
      ..strokeWidth = _strokeWidth
      ..style       = PaintingStyle.stroke;

    final center = Offset(size.width / 2, size.height / 2);
    final radius = (size.width / 2) - _strokeWidth / 2;

    final circumference = 2 * math.pi * radius;
    final dashCount     = (circumference / (_dashLength + _gapLength)).floor();
    if (dashCount == 0) return;

    final stepAngle = (2 * math.pi) / dashCount;
    final dashAngle = stepAngle * (_dashLength / (_dashLength + _gapLength));

    for (int i = 0; i < dashCount; i++) {
      final startAngle = i * stepAngle - math.pi / 2;
      canvas.drawArc(
        Rect.fromCircle(center: center, radius: radius),
        startAngle,
        dashAngle,
        false,
        paint,
      );
    }
  }

  @override
  bool shouldRepaint(_DashedCirclePainter old) => old.color != color;
}
