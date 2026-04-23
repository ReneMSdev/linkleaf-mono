import 'package:flutter/material.dart';
import 'package:qr_flutter/qr_flutter.dart';
import '../../../core/colors.dart';

// TODO: replace with provider data
const mockQrData = 'https://linkleaf.co/q/abc123xyz';

// QR code widget shown in the background of the home screen above the
// profile card. Scales up slightly as the card is dragged down to peek.
class QRZone extends StatelessWidget {
  final String       qrData;
  final double       qrScale;
  final VoidCallback onTap;

  const QRZone({
    required this.qrData,
    required this.qrScale,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return Center(
      child: GestureDetector(
        onTap: onTap,
        child: AnimatedScale(
          scale:    qrScale,
          duration: const Duration(milliseconds: 150),
          child: Container(
            decoration: BoxDecoration(
              color:        AppColors.card,
              borderRadius: BorderRadius.circular(12),
            ),
            padding: const EdgeInsets.all(10),
            child: QrImageView(
              data:            qrData,
              version:         QrVersions.auto,
              size:            128,
              backgroundColor: AppColors.card,
              eyeStyle: const QrEyeStyle(
                eyeShape: QrEyeShape.square,
                color:    AppColors.cardText,
              ),
              dataModuleStyle: const QrDataModuleStyle(
                dataModuleShape: QrDataModuleShape.square,
                color:           AppColors.cardText,
              ),
            ),
          ),
        ),
      ),
    );
  }
}
