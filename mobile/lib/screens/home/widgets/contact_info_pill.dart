// ignore_for_file: unused_element
import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import '../../../core/colors.dart';

// TODO: replace with provider data
// Example values — not used by the widget itself.
const _mockPhone = '+1 (555) 000-0000';
const _mockEmail = 'rene@example.com';

// A full-width pill displaying a contact detail (phone or email)
// with an icon and a mock value. Shown above the links on the profile card.
class ContactInfoPill extends StatelessWidget {
  final IconData icon;
  final String   value;

  const ContactInfoPill({required this.icon, required this.value});

  @override
  Widget build(BuildContext context) {
    return Container(
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
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 11),
        child: Row(
          children: [
            Icon(icon, size: 16, color: AppColors.cardMuted),
            const SizedBox(width: 10),
            Text(
              value,
              style: GoogleFonts.plusJakartaSans(
                fontSize:   14,
                fontWeight: FontWeight.w500,
                color:      AppColors.cardText,
              ),
            ),
          ],
        ),
      ),
    );
  }
}
