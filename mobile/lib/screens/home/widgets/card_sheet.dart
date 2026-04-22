import 'package:flutter/material.dart';
import '../../../core/colors.dart';
import '../../../models/link.dart';
import 'avatar_section.dart';
import 'contact_info_pill.dart';
import 'link_pill.dart';
import 'premium_locked_section.dart';

// Temporary — move to a profile data layer when the API is wired.
const _mockLinks = [
  Link(id: '1', title: 'Portfolio', url: 'https://portfolio.example.com'),
  Link(id: '2', title: 'GitHub', url: 'https://github.com'),
  Link(id: '3', title: 'LinkedIn', url: 'https://linkedin.com'),
  Link(id: '4', title: 'Dribbble', url: 'https://dribbble.com'),
];

// Draggable profile card sheet shown on the home screen and in preview mode.
// Contains the avatar, contact info pills, links, and premium locked sections.
class CardSheet extends StatelessWidget {
  final ScrollController scrollController;
  final VoidCallback onHandleTap;
  final bool profilePreviewLinksLocked;
  final double topCornerRadius;
  final double listTopInset;

  const CardSheet({
    required this.scrollController,
    required this.onHandleTap,
    required this.profilePreviewLinksLocked,
    this.topCornerRadius = 24,
    this.listTopInset = 0,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: BoxDecoration(
        color: AppColors.card,
        borderRadius: BorderRadius.vertical(
          top: Radius.circular(topCornerRadius),
        ),
        boxShadow: const [
          BoxShadow(
            color: Color(0x521A1814),
            blurRadius: 32,
            offset: Offset(0, -8),
          ),
        ],
      ),
      // Always render full content — the sheet height clips naturally at peek.
      child: ListView(
        key: const PageStorageKey<String>('home_profile_card_list'),
        controller: scrollController,
        padding: EdgeInsets.only(top: listTopInset),
        physics: const ClampingScrollPhysics(),
        children: [
          _DragHandle(onTap: onHandleTap),
          const AvatarSection(),
          const Padding(
            padding: EdgeInsets.fromLTRB(20, 0, 20, 10),
            child: Divider(
              height: 1,
              thickness: 1,
              color: AppColors.cardBorder,
            ),
          ),
          const Padding(
            padding: EdgeInsets.fromLTRB(16, 0, 16, 7),
            child: ContactInfoPill(
              icon: Icons.phone_outlined,
              value: '+1 (555) 000-0000',
            ),
          ),
          const Padding(
            padding: EdgeInsets.fromLTRB(16, 0, 16, 7),
            child: ContactInfoPill(
              icon: Icons.mail_outline,
              value: 'rene@example.com',
            ),
          ),
          ..._mockLinks.map(
            (l) => Padding(
              padding: const EdgeInsets.fromLTRB(16, 0, 16, 7),
              child: LinkPill(
                link: l,
                linkPreviewLocked: profilePreviewLinksLocked,
              ),
            ),
          ),
          const SizedBox(height: 12),
          const Padding(
            padding: EdgeInsets.symmetric(horizontal: 16),
            child: PremiumLockedSection(label: 'Portfolio images'),
          ),
          const SizedBox(height: 8),
          const Padding(
            padding: EdgeInsets.symmetric(horizontal: 16),
            child: PremiumLockedSection(label: 'Resume'),
          ),
          const SizedBox(height: 32),
        ],
      ),
    );
  }
}

class _DragHandle extends StatelessWidget {
  final VoidCallback? onTap;
  const _DragHandle({this.onTap});

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      behavior: HitTestBehavior.opaque,
      child: SizedBox(
        height: 28,
        child: Center(
          child: Container(
            width: 32,
            height: 4,
            decoration: BoxDecoration(
              color: AppColors.cardBorder,
              borderRadius: BorderRadius.circular(2),
            ),
          ),
        ),
      ),
    );
  }
}
