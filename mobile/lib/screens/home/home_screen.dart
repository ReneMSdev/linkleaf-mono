import 'dart:ui' show lerpDouble;

import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:qr_flutter/qr_flutter.dart';
import 'package:url_launcher/url_launcher.dart';
import '../../core/colors.dart';
import '../../models/link.dart';

// ── Snap constants (fractions of sheet parent height) ─────────────────────

const _kPeek = 0.065; // ~drag handle strip only
const _kMid  = 0.55;  // default — card at ~55 %
const _kTop  = 0.93;  // card covers QR zone

const _kNavBarHeight = 62.0;

enum _Pos { peek, mid, top }

enum _PreviewPhase {
  idle,
  animatingIn,
  ready,
  animatingOutUi,
  animatingOutSheet,
}

// ── Mock data — replaced when GET /v1/profiles is wired ──────────────────

const _mockQrToken = 'abc123xyz';
const _mockSlug    = 'rene-v';

/// Placeholder until GET /v1/profiles provides id.
const _mockProfileId = 'mock-profile-id';

/// Placeholder until profile payload includes this flag.
const _mockHasSensitiveData = true;

const _apiBase = String.fromEnvironment(
  'LINKLEAF_API_BASE',
  defaultValue: 'https://api.linkleaf.co',
);

const _mockLinks = [
  Link(id: '1', title: 'Portfolio', url: 'https://portfolio.example.com'),
  Link(id: '2', title: 'GitHub',    url: 'https://github.com'),
  Link(id: '3', title: 'LinkedIn',  url: 'https://linkedin.com'),
  Link(id: '4', title: 'Dribbble',  url: 'https://dribbble.com'),
];

// ── Screen ────────────────────────────────────────────────────────────────

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> with TickerProviderStateMixin {
  final _sheetController = DraggableScrollableController();
  late final AnimationController _previewExpandController;
  late final AnimationController _previewExitUiController;
  late final CurvedAnimation       _previewExpandCurve;
  final ScrollController _previewScrollController = ScrollController();

  _Pos   _pos         = _Pos.mid;
  double _sheetExtent = _kMid;
  int    _navIndex    = 0;

  _PreviewPhase _previewPhase = _PreviewPhase.idle;
  _Pos          _previewEntryPosition = _Pos.mid;
  double        _previewEntryExtent   = _kMid;
  double        _cardScrollPixels       = 0;

  // Tracks extent at pointer-down to decide whether a release is a drag end.
  double? _dragStartExtent;

  // ── QR scale ─────────────────────────────────────────────────────────

  // Smoothly scales 1.0 → 1.15 as the sheet moves from mid down to peek.
  double get _qrScale {
    if (_sheetExtent >= _kMid) return 1.0;
    final t = (_kMid - _sheetExtent) / (_kMid - _kPeek);
    return 1.0 + 0.15 * t.clamp(0.0, 1.0);
  }

  // ── Snap helpers ──────────────────────────────────────────────────────

  _Pos _nearestPos(double extent) {
    final d = {
      _Pos.peek: (extent - _kPeek).abs(),
      _Pos.mid:  (extent - _kMid).abs(),
      _Pos.top:  (extent - _kTop).abs(),
    };
    return d.entries.reduce((a, b) => a.value < b.value ? a : b).key;
  }

  void _snapTo(_Pos pos) {
    final size = switch (pos) {
      _Pos.peek => _kPeek,
      _Pos.mid  => _kMid,
      _Pos.top  => _kTop,
    };
    setState(() {
      _pos         = pos;
      _sheetExtent = size;
    });
    if (!_sheetController.isAttached) return;
    _sheetController.animateTo(
      size,
      duration: const Duration(milliseconds: 420),
      curve: Curves.easeOutBack, // spring overshoot
    );
  }

  bool get _previewCardActive => _previewPhase != _PreviewPhase.idle;

  bool get _previewChromeInteractive =>
      _previewPhase == _PreviewPhase.ready ||
      _previewPhase == _PreviewPhase.animatingOutUi;

  double _chromeOpacity() {
    final linearExpand = _previewExpandController.value;
    switch (_previewPhase) {
      case _PreviewPhase.idle:
      case _PreviewPhase.animatingOutSheet:
        return 0;
      case _PreviewPhase.animatingIn:
        return const Interval(200 / 350, 1.0).transform(linearExpand);
      case _PreviewPhase.ready:
        return 1;
      case _PreviewPhase.animatingOutUi:
        return 1 - _previewExitUiController.value;
    }
  }

  void _onPreviewExpandStatus(AnimationStatus status) {
    if (status == AnimationStatus.completed &&
        _previewPhase == _PreviewPhase.animatingIn) {
      setState(() => _previewPhase = _PreviewPhase.ready);
    }
    if (status == AnimationStatus.dismissed &&
        _previewPhase == _PreviewPhase.animatingOutSheet) {
      setState(() => _previewPhase = _PreviewPhase.idle);
      WidgetsBinding.instance.addPostFrameCallback((_) {
        if (!mounted || !_sheetController.isAttached) return;
        _sheetController.jumpTo(_previewEntryExtent);
      });
    }
  }

  void _onPreviewExitUiStatus(AnimationStatus status) {
    if (status != AnimationStatus.completed) return;
    if (_previewPhase != _PreviewPhase.animatingOutUi) return;
    setState(() => _previewPhase = _PreviewPhase.animatingOutSheet);
    _previewExitUiController.reset();
    _previewExpandController.reverse();
  }

  Future<void> _openVcard() async {
    final uri = Uri.parse('$_apiBase/contacts/$_mockProfileId/vcard');
    if (await canLaunchUrl(uri)) {
      await launchUrl(uri, mode: LaunchMode.externalApplication);
    }
  }

  void _onEyeTap() {
    if (_previewPhase != _PreviewPhase.idle) return;
    _previewEntryPosition = _pos;
    _previewEntryExtent = _sheetController.isAttached
        ? _sheetController.size
        : _sheetExtent;
    setState(() => _previewPhase = _PreviewPhase.animatingIn);
    _previewExpandController.forward(from: 0);
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (!mounted || !_previewScrollController.hasClients) return;
      _previewScrollController.jumpTo(_cardScrollPixels);
    });
  }

  void _onPreviewClose() {
    if (_previewPhase != _PreviewPhase.ready) return;
    setState(() => _previewPhase = _PreviewPhase.animatingOutUi);
    _previewExitUiController.forward(from: 0);
  }

  Color _previewBannerBg(BuildContext context) {
    final dark = Theme.of(context).brightness == Brightness.dark;
    return dark ? AppColors.accent : const Color(0xFF8A7560);
  }

  // ── Lifecycle ─────────────────────────────────────────────────────────

  @override
  void initState() {
    super.initState();
    _previewExpandController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 350),
    )..addStatusListener(_onPreviewExpandStatus);
    _previewExitUiController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 100),
    )..addStatusListener(_onPreviewExitUiStatus);
    _previewExpandCurve = CurvedAnimation(
      parent: _previewExpandController,
      curve: Curves.easeInOutCubic,
    );
  }

  @override
  void dispose() {
    _previewExpandCurve.dispose();
    _previewExpandController.dispose();
    _previewExitUiController.dispose();
    _previewScrollController.dispose();
    _sheetController.dispose();
    super.dispose();
  }

  // ── Build ─────────────────────────────────────────────────────────────

  @override
  Widget build(BuildContext context) {
    final mq     = MediaQuery.of(context);
    final topPad = mq.padding.top;
    final botPad = mq.padding.bottom;

    return Scaffold(
      backgroundColor: AppColors.bg,
      body: AnimatedBuilder(
        animation: Listenable.merge([
          _previewExpandController,
          _previewExitUiController,
        ]),
        builder: (context, _) {
          final screenH  = mq.size.height;
          final navH     = _kNavBarHeight + botPad;
          final bodyH    = screenH - navH;
          final expandT  = _previewExpandCurve.value;
          final topStart = bodyH * (1 - _previewEntryExtent);
          final hStart   = _previewEntryExtent * bodyH;
          final cardTop  = lerpDouble(topStart, 0, expandT)!;
          final cardH    = lerpDouble(hStart, screenH, expandT)!;
          final radius   = lerpDouble(24, 0, expandT)!;
          final chromeOp = _chromeOpacity();

          return Stack(
            clipBehavior: Clip.none,
            children: [
              // QR zone — ends above bottom nav
              Positioned(
                top:    0,
                left:   0,
                right:  0,
                bottom: navH,
                child: Column(
                  children: [
                    SizedBox(height: topPad + 50),
                    Expanded(
                      child: _QRZone(
                        qrData:  'https://linkleaf.co/q/$_mockQrToken',
                        slug:    _mockSlug,
                        pos:     _pos,
                        qrScale: _qrScale,
                        onTap:   () => _snapTo(_Pos.peek),
                      ),
                    ),
                  ],
                ),
              ),

              // Top bar
              Positioned(
                top: topPad, left: 0, right: 0, height: 50,
                child: IgnorePointer(
                  ignoring: _previewCardActive,
                  child: _TopBar(slug: _mockSlug, onEyeTap: _onEyeTap),
                ),
              ),

              // Bottom nav (same widget as before; lives in stack for z-order)
              Positioned(
                left:   0,
                right:  0,
                bottom: 0,
                height: navH,
                child: IgnorePointer(
                  ignoring: _previewCardActive,
                  child: _BottomNav(
                    currentIndex: _navIndex,
                    bottomPad:    botPad,
                    onTap:        (i) => setState(() => _navIndex = i),
                  ),
                ),
              ),

              // Draggable sheet — only while not using the preview morph layer
              if (!_previewCardActive)
                Positioned(
                  top:    0,
                  left:   0,
                  right:  0,
                  bottom: navH,
                  child: Listener(
                    onPointerDown: (_) {
                      if (_sheetController.isAttached) {
                        _dragStartExtent = _sheetController.size;
                      }
                    },
                    onPointerUp: (_) {
                      final start = _dragStartExtent;
                      _dragStartExtent = null;
                      if (start == null || !_sheetController.isAttached) return;
                      if ((_sheetController.size - start).abs() > 0.015) {
                        _snapTo(_nearestPos(_sheetController.size));
                      }
                    },
                    child: NotificationListener<DraggableScrollableNotification>(
                      onNotification: (n) {
                        setState(() {
                          _sheetExtent = n.extent;
                          _pos         = _nearestPos(n.extent);
                        });
                        return false;
                      },
                      child: DraggableScrollableSheet(
                        controller:       _sheetController,
                        initialChildSize: _kMid,
                        minChildSize:     _kPeek,
                        maxChildSize:     _kTop,
                        snap:             false,
                        builder: (context, scrollController) {
                          return NotificationListener<ScrollNotification>(
                            onNotification: (n) {
                              if (n is ScrollUpdateNotification &&
                                  n.metrics.axis == Axis.vertical) {
                                _cardScrollPixels = n.metrics.pixels;
                              }
                              return false;
                            },
                            child: _CardSheet(
                              scrollController: scrollController,
                              onHandleTap: () {
                                if (_pos == _Pos.peek) _snapTo(_Pos.mid);
                              },
                              profilePreviewLinksLocked: false,
                              saveContactEnabled:       false,
                              onSaveContact:             null,
                            ),
                          );
                        },
                      ),
                    ),
                  ),
                ),

              // Profile preview morph + chrome
              if (_previewCardActive)
                Positioned(
                  key:    ValueKey(_previewEntryPosition),
                  top:    cardTop,
                  left:   0,
                  right:  0,
                  height: cardH,
                  child: ClipRRect(
                    borderRadius: BorderRadius.vertical(
                      top: Radius.circular(radius),
                    ),
                    child: Stack(
                      fit: StackFit.expand,
                      children: [
                        NotificationListener<ScrollNotification>(
                          onNotification: (n) {
                            if (n is ScrollUpdateNotification &&
                                n.metrics.axis == Axis.vertical) {
                              _cardScrollPixels = n.metrics.pixels;
                            }
                            return false;
                          },
                          child: _CardSheet(
                            scrollController: _previewScrollController,
                            onHandleTap: () {},
                            profilePreviewLinksLocked: true,
                            saveContactEnabled: _previewChromeInteractive,
                            onSaveContact:      _openVcard,
                            topCornerRadius:    radius,
                          ),
                        ),
                        IgnorePointer(
                          ignoring: chromeOp < 0.01,
                          child: Opacity(
                            opacity: chromeOp,
                            child: Stack(
                              fit: StackFit.expand,
                              children: [
                                Positioned(
                                  top:   0,
                                  left:  0,
                                  right: 0,
                                  child: _PreviewBanner(
                                    background: _previewBannerBg(context),
                                    showSensitiveLine: _mockHasSensitiveData,
                                    onBanner: Theme.of(context).brightness ==
                                            Brightness.dark
                                        ? AppColors.cardText
                                        : Colors.white,
                                    onBannerMuted:
                                        Theme.of(context).brightness ==
                                                Brightness.dark
                                            ? AppColors.cardMuted
                                            : const Color(0xE6FFFFFF),
                                  ),
                                ),
                                Positioned(
                                  right:  mq.padding.right + 16,
                                  bottom: mq.padding.bottom + 16,
                                  child: _PreviewCloseButton(
                                    onTap: _onPreviewClose,
                                  ),
                                ),
                              ],
                            ),
                          ),
                        ),
                      ],
                    ),
                  ),
                ),
            ],
          );
        },
      ),
    );
  }
}

// ── Preview chrome ─────────────────────────────────────────────────────────

class _PreviewBanner extends StatelessWidget {
  final Color   background;
  final bool    showSensitiveLine;
  final Color   onBanner;
  final Color   onBannerMuted;

  const _PreviewBanner({
    required this.background,
    required this.showSensitiveLine,
    required this.onBanner,
    required this.onBannerMuted,
  });

  @override
  Widget build(BuildContext context) {
    return ColoredBox(
      color: background,
      child: SafeArea(
        bottom: false,
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              Text(
                'Previewing your public profile',
                textAlign: TextAlign.center,
                style: GoogleFonts.plusJakartaSans(
                  fontSize:    12,
                  fontWeight:  FontWeight.w500,
                  color:       onBanner,
                  height:      1.2,
                ),
              ),
              if (showSensitiveLine) ...[
                const SizedBox(height: 4),
                Text(
                  'Includes contact info',
                  textAlign: TextAlign.center,
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
      ),
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

// ── QR Zone ───────────────────────────────────────────────────────────────

class _QRZone extends StatelessWidget {
  final String       qrData;
  final String       slug;
  final _Pos         pos;
  final double       qrScale;
  final VoidCallback onTap;

  const _QRZone({
    required this.qrData,
    required this.slug,
    required this.pos,
    required this.qrScale,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    final isPeek = pos == _Pos.peek;

    return Center(
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          GestureDetector(
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
          const SizedBox(height: 8),
          Text(
            'linkleaf.co/q/$slug',
            style: GoogleFonts.plusJakartaSans(
              fontSize: 11,
              color:    AppColors.muted,
            ),
          ),
          const SizedBox(height: 4),
          AnimatedSwitcher(
            duration: const Duration(milliseconds: 200),
            child: Text(
              isPeek ? 'tap card to return' : 'drag up for profile',
              key: ValueKey(isPeek),
              style: GoogleFonts.plusJakartaSans(
                fontSize: 11,
                color:    const Color(0x998C8478),
              ),
            ),
          ),
        ],
      ),
    );
  }
}

// ── Card sheet ────────────────────────────────────────────────────────────

class _CardSheet extends StatelessWidget {
  final ScrollController scrollController;
  final VoidCallback     onHandleTap;
  final bool             profilePreviewLinksLocked;
  final bool             saveContactEnabled;
  final Future<void> Function()? onSaveContact;
  final double           topCornerRadius;

  const _CardSheet({
    required this.scrollController,
    required this.onHandleTap,
    required this.profilePreviewLinksLocked,
    required this.saveContactEnabled,
    required this.onSaveContact,
    this.topCornerRadius = 24,
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
            color:      Color(0x521A1814),
            blurRadius: 32,
            offset:     Offset(0, -8),
          ),
        ],
      ),
      // Always render full content — the sheet height clips naturally at peek.
      child: ListView(
        key:        const PageStorageKey<String>('home_profile_card_list'),
        controller: scrollController,
        padding:    EdgeInsets.zero,
        physics:    const ClampingScrollPhysics(),
        children: [
          _DragHandle(onTap: onHandleTap),
          const _AvatarSection(),
          const Padding(
            padding: EdgeInsets.fromLTRB(20, 0, 20, 10),
            child: Divider(height: 1, thickness: 1, color: AppColors.cardBorder),
          ),
          ..._mockLinks.map(
            (l) => Padding(
              padding: const EdgeInsets.fromLTRB(16, 0, 16, 7),
              child: _LinkPill(
                link:                 l,
                linkPreviewLocked:    profilePreviewLinksLocked,
              ),
            ),
          ),
          const SizedBox(height: 4),
          _ContactChips(
            profilePreviewLinksLocked: profilePreviewLinksLocked,
            saveContactEnabled:        saveContactEnabled,
            onSaveContact:             onSaveContact,
          ),
          const SizedBox(height: 12),
          const Padding(
            padding: EdgeInsets.symmetric(horizontal: 16),
            child: _PremiumLockedSection(label: 'Portfolio images'),
          ),
          const SizedBox(height: 8),
          const Padding(
            padding: EdgeInsets.symmetric(horizontal: 16),
            child: _PremiumLockedSection(label: 'Resume'),
          ),
          const SizedBox(height: 32),
        ],
      ),
    );
  }
}

// ── Drag handle ───────────────────────────────────────────────────────────

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
              color:        AppColors.cardBorder,
              borderRadius: BorderRadius.circular(2),
            ),
          ),
        ),
      ),
    );
  }
}

// ── Avatar section ────────────────────────────────────────────────────────

class _AvatarSection extends StatelessWidget {
  const _AvatarSection();

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.fromLTRB(0, 4, 0, 14),
      child: Column(
        children: [
          Container(
            width: 68, height: 68,
            decoration: const BoxDecoration(
              shape: BoxShape.circle,
              gradient: LinearGradient(
                begin: Alignment.topLeft,
                end:   Alignment.bottomRight,
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
                    color: const Color(0xFF8C7E6E),
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
              color:    AppColors.cardText,
              height:   1.1,
            ),
          ),
          const SizedBox(height: 2),
          Text(
            'Product Designer · Salo Labs',
            style: GoogleFonts.plusJakartaSans(
              fontSize: 13,
              color:    AppColors.cardMuted,
            ),
          ),
          const SizedBox(height: 4),
          Text(
            '143 views',
            style: GoogleFonts.plusJakartaSans(
              fontSize: 11,
              color: const Color(0x998C8070),
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
  final bool linkPreviewLocked;

  const _LinkPill({
    required this.link,
    this.linkPreviewLocked = false,
  });

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
          onTap: linkPreviewLocked ? null : () {}, // tracking only — no navigation yet
          child: Padding(
            padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 11),
            child: Row(
              children: [
                Container(
                  width: 24, height: 24,
                  decoration: BoxDecoration(
                    color:        _iconBg,
                    borderRadius: BorderRadius.circular(6),
                  ),
                  child: Center(
                    child: Container(
                      width: 10, height: 10,
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
    return Opacity(opacity: 0.5, child: IgnorePointer(child: content));
  }
}

// ── Contact chips ─────────────────────────────────────────────────────────

class _ContactChips extends StatelessWidget {
  final bool profilePreviewLinksLocked;
  final bool saveContactEnabled;
  final Future<void> Function()? onSaveContact;

  const _ContactChips({
    required this.profilePreviewLinksLocked,
    required this.saveContactEnabled,
    required this.onSaveContact,
  });

  @override
  Widget build(BuildContext context) {
    final locked = profilePreviewLinksLocked;
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 16),
      child: Row(
        children: [
          Expanded(
            child: _ContactChip(
              label: 'Email',
              icon:  Icons.mail_outline,
              locked: locked,
            ),
          ),
          const SizedBox(width: 8),
          Expanded(
            child: _ContactChip(
              label: 'Phone',
              icon:  Icons.phone_outlined,
              locked: locked,
            ),
          ),
          const SizedBox(width: 8),
          Expanded(
            child: _ContactChip(
              label:         'Save contact',
              icon:          Icons.person_add_outlined,
              locked:        locked && !saveContactEnabled,
              onTapEnabled: saveContactEnabled && onSaveContact != null,
              onChipTap:    onSaveContact,
            ),
          ),
        ],
      ),
    );
  }
}

class _ContactChip extends StatelessWidget {
  final String   label;
  final IconData icon;
  final bool     locked;
  final bool     onTapEnabled;
  final Future<void> Function()? onChipTap;

  const _ContactChip({
    required this.label,
    required this.icon,
    this.locked = false,
    this.onTapEnabled = true,
    this.onChipTap,
  });

  @override
  Widget build(BuildContext context) {
    VoidCallback? inkTap;
    if (locked) {
      inkTap = null;
    } else if (onTapEnabled && onChipTap != null) {
      final fn = onChipTap!;
      inkTap = () {
        fn();
      };
    } else {
      inkTap = () {};
    }

    final child = Container(
      height: 38,
      decoration: BoxDecoration(
        color:        AppColors.cardSub,
        border:       Border.all(color: AppColors.cardBorder),
        borderRadius: BorderRadius.circular(10),
      ),
      child: Material(
        color: Colors.transparent,
        child: InkWell(
          borderRadius: BorderRadius.circular(10),
          onTap: inkTap,
          child: Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Icon(icon, size: 13, color: AppColors.cardMuted),
              const SizedBox(width: 4),
              Text(
                label,
                style: GoogleFonts.plusJakartaSans(
                  fontSize:   11,
                  fontWeight: FontWeight.w500,
                  color:      AppColors.cardMuted,
                ),
              ),
            ],
          ),
        ),
      ),
    );
    if (!locked) return child;
    return Opacity(opacity: 0.5, child: IgnorePointer(child: child));
  }
}

// ── Premium locked section ────────────────────────────────────────────────

class _PremiumLockedSection extends StatelessWidget {
  final String label;
  const _PremiumLockedSection({required this.label});

  @override
  Widget build(BuildContext context) {
    return Container(
      height: 68,
      decoration: BoxDecoration(
        color:        AppColors.cardSub,
        border:       Border.all(color: AppColors.cardBorder),
        borderRadius: BorderRadius.circular(12),
      ),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          const Icon(Icons.lock_outline, size: 15, color: AppColors.cardBorder),
          const SizedBox(width: 8),
          Text(
            label,
            style: GoogleFonts.plusJakartaSans(
              fontSize: 13,
              color:    AppColors.cardBorder,
            ),
          ),
          Text(
            ' · Premium',
            style: GoogleFonts.plusJakartaSans(
              fontSize: 12,
              color:    const Color(0xFFD0C8BC),
            ),
          ),
        ],
      ),
    );
  }
}

// ── Top bar ───────────────────────────────────────────────────────────────

class _TopBar extends StatelessWidget {
  final String       slug;
  final VoidCallback onEyeTap;
  const _TopBar({required this.slug, required this.onEyeTap});

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
              '@$slug',
              style: GoogleFonts.plusJakartaSans(
                fontSize:    13,
                fontWeight:  FontWeight.w500,
                color:       AppColors.muted,
                letterSpacing: 0.2,
              ),
            ),
            const Spacer(),
            GestureDetector(
              onTap:     onEyeTap,
              behavior:  HitTestBehavior.opaque,
              child: const SizedBox(
                width: 36, height: 36,
                child: Center(
                  child: Icon(
                    Icons.remove_red_eye_outlined,
                    color: AppColors.muted,
                    size:  22,
                  ),
                ),
              ),
            ),
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
      width: 36, height: 36,
      child: Column(
        mainAxisAlignment:  MainAxisAlignment.center,
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

// ── Bottom nav ────────────────────────────────────────────────────────────

class _NavTab {
  final String   label;
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
  final int                currentIndex;
  final double             bottomPad;
  final ValueChanged<int>  onTap;

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
        color:  AppColors.surface,
        border: Border(top: BorderSide(color: AppColors.border)),
      ),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceAround,
        children: List.generate(_navTabs.length, (i) {
          final tab    = _navTabs[i];
          final active = i == currentIndex;
          final color  = active ? AppColors.accent : AppColors.muted;
          return GestureDetector(
            onTap:    () => onTap(i),
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
                      fontSize:   10,
                      fontWeight: active ? FontWeight.w600 : FontWeight.w400,
                      color:      color,
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
