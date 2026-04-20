import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:qr_flutter/qr_flutter.dart';
import '../../core/colors.dart';
import '../../models/link.dart';

const _mockLinks = [
  Link(id: '1', title: 'Portfolio', url: 'https://portfolio.example.com'),
  Link(id: '2', title: 'GitHub', url: 'https://github.com'),
  Link(id: '3', title: 'LinkedIn', url: 'https://linkedin.com'),
  Link(id: '4', title: 'Dribbble', url: 'https://dribbble.com'),
];

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  int _navIndex = 0;

  @override
  Widget build(BuildContext context) {
    final bottomPad = MediaQuery.of(context).padding.bottom;
    return Scaffold(
      backgroundColor: AppColors.bg,
      body: Column(
        children: [
          SizedBox(height: MediaQuery.of(context).padding.top),
          const _TopBar(),
          const _QRZone(),
          const Expanded(child: _ProfileCard()),
        ],
      ),
      bottomNavigationBar: _BottomNav(
        currentIndex: _navIndex,
        bottomPad: bottomPad,
        onTap: (i) => setState(() => _navIndex = i),
      ),
    );
  }
}

// ── Top bar ───────────────────────────────────────────────────────────────

class _TopBar extends StatelessWidget {
  const _TopBar();

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      height: 50,
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 16),
        child: Row(
          children: [
            const _HamburgerIcon(),
            const Spacer(),
            Text(
              '@rene-v',
              style: GoogleFonts.plusJakartaSans(
                fontSize: 13,
                fontWeight: FontWeight.w500,
                color: AppColors.muted,
                letterSpacing: 0.2,
              ),
            ),
            const Spacer(),
            const _EyeIcon(),
          ],
        ),
      ),
    );
  }
}

class _HamburgerIcon extends StatelessWidget {
  const _HamburgerIcon();

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      width: 36,
      height: 36,
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Container(width: 22, height: 1.5, color: AppColors.text),
          const SizedBox(height: 5),
          Container(width: 16, height: 1.5, color: AppColors.muted),
        ],
      ),
    );
  }
}

class _EyeIcon extends StatelessWidget {
  const _EyeIcon();

  @override
  Widget build(BuildContext context) {
    return const SizedBox(
      width: 36,
      height: 36,
      child: Center(
        child: Icon(Icons.remove_red_eye_outlined, color: AppColors.muted, size: 22),
      ),
    );
  }
}

// ── QR zone ───────────────────────────────────────────────────────────────

class _QRZone extends StatelessWidget {
  const _QRZone();

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      height: 165,
      child: Center(
        child: Container(
          decoration: BoxDecoration(
            color: AppColors.card,
            borderRadius: BorderRadius.circular(12),
          ),
          padding: const EdgeInsets.all(8),
          child: QrImageView(
            data: 'https://linkleaf.co/@rene-v',
            version: QrVersions.auto,
            size: 120,
            backgroundColor: AppColors.card,
            eyeStyle: const QrEyeStyle(
              eyeShape: QrEyeShape.square,
              color: AppColors.cardText,
            ),
            dataModuleStyle: const QrDataModuleStyle(
              dataModuleShape: QrDataModuleShape.square,
              color: AppColors.cardText,
            ),
          ),
        ),
      ),
    );
  }
}

// ── Profile card ──────────────────────────────────────────────────────────

class _ProfileCard extends StatelessWidget {
  const _ProfileCard();

  @override
  Widget build(BuildContext context) {
    return Stack(
      children: [
        Container(
          decoration: const BoxDecoration(
            color: AppColors.card,
            borderRadius: BorderRadius.only(
              topLeft: Radius.circular(24),
              topRight: Radius.circular(24),
            ),
            boxShadow: [
              BoxShadow(
                color: Color(0x521A1814),
                blurRadius: 32,
                offset: Offset(0, -8),
              ),
            ],
          ),
          child: Column(
            children: [
              // Drag handle
              Padding(
                padding: const EdgeInsets.fromLTRB(0, 10, 0, 6),
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
              // Avatar + name
              const _AvatarSection(),
              // Divider
              const Padding(
                padding: EdgeInsets.fromLTRB(20, 0, 20, 12),
                child: Divider(height: 1, thickness: 1, color: AppColors.cardBorder),
              ),
              // Links
              Expanded(
                child: ListView.builder(
                  padding: const EdgeInsets.fromLTRB(16, 0, 16, 80),
                  itemCount: _mockLinks.length,
                  itemBuilder: (_, i) => _LinkPill(link: _mockLinks[i]),
                ),
              ),
            ],
          ),
        ),
        const Positioned(
          bottom: 16,
          right: 16,
          child: _EditFAB(),
        ),
      ],
    );
  }
}

class _AvatarSection extends StatelessWidget {
  const _AvatarSection();

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.fromLTRB(0, 6, 0, 12),
      child: Column(
        children: [
          Container(
            width: 68,
            height: 68,
            decoration: const BoxDecoration(
              shape: BoxShape.circle,
              gradient: LinearGradient(
                begin: Alignment.topLeft,
                end: Alignment.bottomRight,
                colors: [Color(0x55C9B99A), Color(0x22C9B99A)],
              ),
            ),
            padding: const EdgeInsets.all(2),
            child: Container(
              decoration: const BoxDecoration(
                shape: BoxShape.circle,
                color: Color(0xFFD8CFC4),
              ),
              child: Center(
                child: Text(
                  'RV',
                  style: GoogleFonts.plusJakartaSans(
                    fontSize: 22,
                    fontWeight: FontWeight.w700,
                    color: Color(0xFF8C7E6E),
                  ),
                ),
              ),
            ),
          ),
          const SizedBox(height: 8),
          Text(
            'René Villanueva',
            style: GoogleFonts.plusJakartaSans(
              fontSize: 18,
              fontWeight: FontWeight.w700,
              color: AppColors.cardText,
              height: 1.1,
            ),
          ),
          const SizedBox(height: 2),
          Text(
            'Product Designer · Salo Labs',
            style: GoogleFonts.plusJakartaSans(
              fontSize: 13,
              color: AppColors.cardMuted,
            ),
          ),
          const SizedBox(height: 3),
          Text(
            '143 views',
            style: GoogleFonts.plusJakartaSans(
              fontSize: 11,
              color: Color(0x998C8070),
            ),
          ),
        ],
      ),
    );
  }
}

// ── Link pill ─────────────────────────────────────────────────────────────

class _LinkPill extends StatelessWidget {
  final Link link;
  const _LinkPill({required this.link});

  Color get _iconColor {
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
    return Container(
      margin: const EdgeInsets.only(bottom: 7),
      decoration: BoxDecoration(
        color: AppColors.card,
        border: Border.all(color: AppColors.cardBorder),
        borderRadius: BorderRadius.circular(12),
        boxShadow: const [
          BoxShadow(
            color: Color(0x0F1A1814),
            blurRadius: 3,
            offset: Offset(0, 1),
          ),
        ],
      ),
      child: Material(
        color: Colors.transparent,
        child: InkWell(
          borderRadius: BorderRadius.circular(12),
          onTap: () {},
          child: Padding(
            padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 11),
            child: Row(
              children: [
                Container(
                  width: 24,
                  height: 24,
                  decoration: BoxDecoration(
                    color: _iconColor,
                    borderRadius: BorderRadius.circular(6),
                  ),
                  child: Center(
                    child: Container(
                      width: 10,
                      height: 10,
                      decoration: BoxDecoration(
                        color: const Color(0xE5FFFFFF),
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
                      fontSize: 14,
                      fontWeight: FontWeight.w500,
                      color: AppColors.cardText,
                    ),
                  ),
                ),
                const Icon(
                  Icons.chevron_right,
                  size: 16,
                  color: Color(0x4D1A1814),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}

// ── Edit FAB ──────────────────────────────────────────────────────────────

class _EditFAB extends StatelessWidget {
  const _EditFAB();

  @override
  Widget build(BuildContext context) {
    return Container(
      width: 44,
      height: 44,
      decoration: const BoxDecoration(
        color: AppColors.cardText,
        shape: BoxShape.circle,
        boxShadow: [
          BoxShadow(
            color: Color(0x381A1814),
            blurRadius: 16,
            offset: Offset(0, 4),
          ),
          BoxShadow(
            color: Color(0x1F1A1814),
            blurRadius: 4,
            offset: Offset(0, 1),
          ),
        ],
      ),
      child: const Icon(Icons.edit_outlined, color: AppColors.card, size: 16),
    );
  }
}

// ── Bottom nav ────────────────────────────────────────────────────────────

class _NavTab {
  final String label;
  final IconData icon;
  final IconData activeIcon;
  const _NavTab(this.label, this.icon, this.activeIcon);
}

const _navTabs = [
  _NavTab('Home',     Icons.home_outlined,    Icons.home),
  _NavTab('Profiles', Icons.person_outline,   Icons.person),
  _NavTab('Themes',   Icons.palette_outlined, Icons.palette),
];

class _BottomNav extends StatelessWidget {
  final int currentIndex;
  final double bottomPad;
  final ValueChanged<int> onTap;

  const _BottomNav({
    required this.currentIndex,
    required this.bottomPad,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      height: 62 + bottomPad,
      decoration: const BoxDecoration(
        color: AppColors.surface,
        border: Border(top: BorderSide(color: AppColors.border)),
      ),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceAround,
        children: List.generate(_navTabs.length, (i) {
          final tab = _navTabs[i];
          final active = i == currentIndex;
          final color = active ? AppColors.accent : AppColors.muted;
          return GestureDetector(
            onTap: () => onTap(i),
            behavior: HitTestBehavior.opaque,
            child: SizedBox(
              width: 72,
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Icon(active ? tab.activeIcon : tab.icon, size: 20, color: color),
                  const SizedBox(height: 3),
                  Text(
                    tab.label,
                    style: GoogleFonts.plusJakartaSans(
                      fontSize: 10,
                      fontWeight: active ? FontWeight.w600 : FontWeight.w400,
                      color: color,
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
