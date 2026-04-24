import 'package:flutter/material.dart';
import '../../../core/colors.dart';
import '../../../models/link.dart';
import 'avatar_image.dart';
import 'contact_info_pill.dart';
import 'profile_info.dart';
import 'link_pill.dart';
import 'linkleaf_branding.dart';
import 'portfolio_carousel.dart';
import 'premium_locked_section.dart';
import 'resume_widget.dart';

// TODO: replace with provider data
const mockDisplayName    = 'René Villanueva';
const mockInitials       = 'RV';
const mockTitle          = 'Product Designer';
const mockCompany        = 'Salo Labs';
const mockViewCount      = 143;
const mockPhone          = '+1 (555) 000-0000';
const mockEmail          = 'rene@example.com';
const mockHasSensitiveData = true;
const mockLinks = [
  Link(id: '1', title: 'Portfolio', url: 'https://portfolio.example.com'),
  Link(id: '2', title: 'GitHub',    url: 'https://github.com'),
  Link(id: '3', title: 'LinkedIn',  url: 'https://linkedin.com'),
  Link(id: '4', title: 'Dribbble',  url: 'https://dribbble.com'),
];

// Draggable profile card sheet shown on the home screen and in preview mode.
// isPremium drives all conditional UI — matches the premium entitlement field
// the API returns, exposed via SubscriptionProvider once wired up.
class CardSheet extends StatelessWidget {
  final ScrollController scrollController;
  final VoidCallback     onHandleTap;
  final bool             profilePreviewLinksLocked;
  final double           topCornerRadius;
  final double           listTopInset;
  final double           listBottomInset;
  final bool             showDragHandle;
  // true  → premium: portfolio carousel, résumé widget
  // false → free:    branding bar, locked placeholders
  final bool             isPremium;
  final String           displayName;
  final String           initials;
  final String           title;
  final String           company;
  final int              viewCount;
  final List<Link>       links;
  final bool             hasSensitiveData;
  final String?          phone;
  final String?          email;

  const CardSheet({
    required this.scrollController,
    required this.onHandleTap,
    required this.profilePreviewLinksLocked,
    this.topCornerRadius = 24,
    this.listTopInset    = 0,
    this.listBottomInset = 0,
    this.showDragHandle  = true,
    this.isPremium       = false,
    required this.displayName,
    required this.initials,
    required this.title,
    required this.company,
    required this.viewCount,
    required this.links,
    required this.hasSensitiveData,
    this.phone,
    this.email,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      clipBehavior: Clip.hardEdge,
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
      child: ListView(
        key: const PageStorageKey<String>('home_profile_card_list'),
        controller: scrollController,
        padding: EdgeInsets.only(top: listTopInset, bottom: listBottomInset),
        physics: const ClampingScrollPhysics(),
        children: [
          if (showDragHandle) _DragHandle(onTap: onHandleTap),
          if (!isPremium) ...[
            const LinkLeafBranding(),
            const SizedBox(height: 12),
          ],
          Padding(
            padding: const EdgeInsets.fromLTRB(0, 4, 0, 14),
            child: Column(
              children: [
                AvatarImage(initials: initials),
                ProfileInfo(
                  displayName: displayName,
                  title:       title,
                  company:     company,
                  viewCount:   viewCount,
                ),
              ],
            ),
          ),
          const Padding(
            padding: EdgeInsets.fromLTRB(20, 0, 20, 10),
            child: Divider(height: 1, thickness: 1, color: AppColors.cardBorder),
          ),
          if (phone != null)
            Padding(
              padding: const EdgeInsets.fromLTRB(16, 0, 16, 7),
              child: ContactInfoPill(icon: Icons.phone_outlined, value: phone!),
            ),
          if (email != null)
            Padding(
              padding: const EdgeInsets.fromLTRB(16, 0, 16, 7),
              child: ContactInfoPill(icon: Icons.mail_outline, value: email!),
            ),
          ...links.map(
            (l) => Padding(
              padding: const EdgeInsets.fromLTRB(16, 0, 16, 7),
              child: LinkPill(
                link:              l,
                linkPreviewLocked: profilePreviewLinksLocked,
              ),
            ),
          ),
          if (!isPremium) ...[
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
          ] else ...[
            const Padding(
              padding: EdgeInsets.fromLTRB(20, 0, 20, 16),
              child: Divider(height: 1, thickness: 1, color: AppColors.cardBorder),
            ),
            const PortfolioCarousel(),
            const Padding(
              padding: EdgeInsets.fromLTRB(20, 16, 20, 16),
              child: Divider(height: 1, thickness: 1, color: AppColors.cardBorder),
            ),
            const Padding(
              padding: EdgeInsets.symmetric(horizontal: 16),
              child: ResumeWidget(),
            ),
          ],
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
            width:  32,
            height: 4,
            decoration: BoxDecoration(
              color:        AppColors.cardBorder,
              borderRadius: BorderRadius.circular(2),
            ),
          ),
        ),
      ),
    );
  }
}
