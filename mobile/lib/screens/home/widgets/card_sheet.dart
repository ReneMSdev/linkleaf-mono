import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import '../../../core/colors.dart';
import '../../../models/link.dart';
import 'avatar_image.dart';
import 'contact_info_pill.dart';
import 'link_pill.dart';
import 'linkleaf_branding.dart';
import 'portfolio_carousel.dart';
import 'premium_locked_section.dart';
import 'profile_info.dart';
import 'resume_widget.dart';
import 'section_header.dart';

// TODO: replace with provider data
const mockDisplayName      = 'René Villanueva';
const mockInitials         = 'RV';
const mockTitle            = 'Product Designer';
const mockCompany          = 'Salo Labs';
const mockPhone            = '+1 (555) 000-0000';
const mockEmail            = 'rene@example.com';
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
  final bool             editMode;
  final String           displayName;
  final String           initials;
  final String           title;
  final String           company;
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
    this.editMode        = false,
    required this.displayName,
    required this.initials,
    required this.title,
    required this.company,
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
            color:      Color(0x521A1814),
            blurRadius: 32,
            offset:     Offset(0, -8),
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

          // Section: Identity — always first, not removable
          SectionHeader(
            label:          'Identity',
            showLabel:      true,
            editMode:       editMode,
            isFixed:        true,
            onDelete:       () {},
            onToggleLabel:  () {},
            onLabelChanged: (_) {},
            child: Padding(
              padding: const EdgeInsets.fromLTRB(0, 4, 0, 14),
              child: Column(
                children: [
                  AvatarImage(initials: initials, editMode: editMode),
                  ProfileInfo(
                    displayName: displayName,
                    title:       title,
                    company:     company,
                    editMode:    editMode,
                  ),
                ],
              ),
            ),
          ),

          // Separator: divider in view mode, add-section strip in edit mode
          if (!editMode)
            const Padding(
              padding: EdgeInsets.fromLTRB(20, 0, 20, 10),
              child: Divider(height: 1, thickness: 1, color: AppColors.cardBorder),
            )
          else
            _AddSectionDivider(onTap: () => debugPrint('+ Add section tapped')),

          // Section: Contact (only if contact data is present)
          if (phone != null || email != null) ...[
            SectionHeader(
              label:          'Contact',
              showLabel:      true,
              editMode:       editMode,
              onDelete:       () {},
              onToggleLabel:  () {},
              onLabelChanged: (_) {},
              child: Column(
                children: [
                  if (phone != null)
                    Padding(
                      padding: const EdgeInsets.fromLTRB(16, 0, 16, 7),
                      child: ContactInfoPill(
                        icon:  Icons.phone_outlined,
                        value: phone!,
                      ),
                    ),
                  if (email != null)
                    Padding(
                      padding: const EdgeInsets.fromLTRB(16, 0, 16, 7),
                      child: ContactInfoPill(
                        icon:  Icons.mail_outline,
                        value: email!,
                      ),
                    ),
                ],
              ),
            ),
            if (editMode)
              _AddSectionDivider(onTap: () => debugPrint('+ Add section tapped')),
          ],

          // Section: Links
          SectionHeader(
            label:          'Links',
            showLabel:      true,
            editMode:       editMode,
            onDelete:       () {},
            onToggleLabel:  () {},
            onLabelChanged: (_) {},
            child: Column(
              children: links
                  .map(
                    (l) => Padding(
                      padding: const EdgeInsets.fromLTRB(16, 0, 16, 7),
                      child: LinkPill(
                        link:              l,
                        linkPreviewLocked: profilePreviewLinksLocked,
                      ),
                    ),
                  )
                  .toList(),
            ),
          ),

          // Sections: Portfolio + Resume
          if (!isPremium) ...[
            if (!editMode)
              const SizedBox(height: 12)
            else
              _AddSectionDivider(onTap: () => debugPrint('+ Add section tapped')),
            SectionHeader(
              label:          'Portfolio',
              showLabel:      true,
              editMode:       editMode,
              onDelete:       () {},
              onToggleLabel:  () {},
              onLabelChanged: (_) {},
              child: const Padding(
                padding: EdgeInsets.symmetric(horizontal: 16),
                child: PremiumLockedSection(label: 'Portfolio images'),
              ),
            ),
            if (!editMode)
              const SizedBox(height: 8)
            else
              _AddSectionDivider(onTap: () => debugPrint('+ Add section tapped')),
            SectionHeader(
              label:          'Resume',
              showLabel:      true,
              editMode:       editMode,
              onDelete:       () {},
              onToggleLabel:  () {},
              onLabelChanged: (_) {},
              child: const Padding(
                padding: EdgeInsets.symmetric(horizontal: 16),
                child: PremiumLockedSection(label: 'Resume'),
              ),
            ),
          ] else ...[
            if (!editMode)
              const Padding(
                padding: EdgeInsets.fromLTRB(20, 0, 20, 16),
                child: Divider(height: 1, thickness: 1, color: AppColors.cardBorder),
              )
            else
              _AddSectionDivider(onTap: () => debugPrint('+ Add section tapped')),
            SectionHeader(
              label:          'Portfolio',
              showLabel:      true,
              editMode:       editMode,
              onDelete:       () {},
              onToggleLabel:  () {},
              onLabelChanged: (_) {},
              child: const PortfolioCarousel(),
            ),
            if (!editMode)
              const Padding(
                padding: EdgeInsets.fromLTRB(20, 16, 20, 16),
                child: Divider(height: 1, thickness: 1, color: AppColors.cardBorder),
              )
            else
              _AddSectionDivider(onTap: () => debugPrint('+ Add section tapped')),
            SectionHeader(
              label:          'Resume',
              showLabel:      true,
              editMode:       editMode,
              onDelete:       () {},
              onToggleLabel:  () {},
              onLabelChanged: (_) {},
              child: const Padding(
                padding: EdgeInsets.symmetric(horizontal: 16),
                child: ResumeWidget(),
              ),
            ),
          ],

          const SizedBox(height: 32),
        ],
      ),
    );
  }
}

// ── Add section divider ────────────────────────────────────────────────────

class _AddSectionDivider extends StatelessWidget {
  final VoidCallback onTap;
  const _AddSectionDivider({required this.onTap});

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap:    onTap,
      behavior: HitTestBehavior.opaque,
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
        child: Row(
          children: [
            const Expanded(
              child: CustomPaint(
                painter: _DashedLinePainter(),
                child:   SizedBox(height: 1),
              ),
            ),
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 12),
              child: Text(
                '+ Add section',
                style: GoogleFonts.plusJakartaSans(
                  fontSize:   11,
                  fontWeight: FontWeight.w500,
                  color:      AppColors.cardBorder,
                ),
              ),
            ),
            const Expanded(
              child: CustomPaint(
                painter: _DashedLinePainter(),
                child:   SizedBox(height: 1),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _DashedLinePainter extends CustomPainter {
  const _DashedLinePainter();

  @override
  void paint(Canvas canvas, Size size) {
    final paint = Paint()
      ..color       = AppColors.cardBorder
      ..strokeWidth = 1;
    const dashWidth = 4.0;
    const dashSpace = 4.0;
    final y = size.height / 2;
    double x = 0;
    while (x < size.width) {
      canvas.drawLine(Offset(x, y), Offset(x + dashWidth, y), paint);
      x += dashWidth + dashSpace;
    }
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) => false;
}

// ── Drag handle ────────────────────────────────────────────────────────────

class _DragHandle extends StatelessWidget {
  final VoidCallback? onTap;
  const _DragHandle({this.onTap});

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap:    onTap,
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
