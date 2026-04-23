import 'dart:ui' show lerpDouble;

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import '../../core/colors.dart';
import '../../core/constants.dart';
import 'widgets/bottom_nav.dart';
import 'widgets/card_sheet.dart';
import 'widgets/edit_fab.dart';
import 'widgets/preview_banner.dart';
import 'widgets/qr_zone.dart';
import 'widgets/save_contact_fab.dart';
import 'widgets/top_bar.dart';

// _kTop is computed per-layout — see _HomeScreenState._kTop

enum _Pos { peek, mid, top }

enum _PreviewPhase {
  idle,
  animatingIn,
  ready,
  animatingOutUi,
  animatingOutSheet,
}

// Mock data lives in each widget file — see widgets/card_sheet.dart,
// widgets/qr_zone.dart, and widgets/top_bar.dart for the TODO blocks.

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
  late final CurvedAnimation _previewExpandCurve;
  final ScrollController _previewScrollController = ScrollController();

  _Pos   _pos         = _Pos.mid;
  double _sheetExtent = kMid;
  int    _navIndex    = 0;

  // Computed in build() from real screen metrics; fallback keeps things safe
  // before the first layout.
  double _kTop = 0.92;

  _PreviewPhase _previewPhase        = _PreviewPhase.idle;
  _Pos          _previewEntryPosition = _Pos.mid;
  double        _previewEntryExtent   = kMid;
  double _cardScrollPixels = 0;

  // Tracks extent at pointer-down to decide whether a release is a drag end.
  double? _dragStartExtent;

  // ── QR scale ─────────────────────────────────────────────────────────

  // Smoothly scales 1.0 → 1.15 as the sheet moves from mid down to peek.
  double get _qrScale {
    if (_sheetExtent >= kMid) return 1.0;
    final t = (kMid - _sheetExtent) / (kMid - kPeek);
    return 1.0 + 0.15 * t.clamp(0.0, 1.0);
  }

  // ── Snap helpers ──────────────────────────────────────────────────────

  _Pos _nearestPos(double extent) {
    final d = {
      _Pos.peek: (extent - kPeek).abs(),
      _Pos.mid: (extent - kMid).abs(),
      _Pos.top: (extent - _kTop).abs(),
    };
    return d.entries.reduce((a, b) => a.value < b.value ? a : b).key;
  }

  void _snapTo(_Pos pos) {
    final size = switch (pos) {
      _Pos.peek => kPeek,
      _Pos.mid => kMid,
      _Pos.top => _kTop,
    };
    setState(() {
      _pos = pos;
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
      // Restore status bar icons to light for the dark app background.
      SystemChrome.setSystemUIOverlayStyle(SystemUiOverlayStyle.light);
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

  void _onEyeTap() {
    if (_previewPhase != _PreviewPhase.idle) return;
    _previewEntryPosition = _pos;
    _previewEntryExtent = _sheetController.isAttached
        ? _sheetController.size
        : _sheetExtent;
    // Card background is light — switch status bar icons to dark.
    SystemChrome.setSystemUIOverlayStyle(SystemUiOverlayStyle.dark);
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
    final mq = MediaQuery.of(context);
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
          final screenH = mq.size.height;
          final navH    = kNavBarHeight + botPad;
          final bodyH   = screenH - navH;

          // Card stops just below the top bar (status bar + 50px bar + 8px gap).
          final computedTop = ((bodyH - topPad - 50 - 8) / bodyH).clamp(0.5, 0.99);
          if (computedTop != _kTop) _kTop = computedTop;

          final expandT = _previewExpandCurve.value;
          final topStart = bodyH * (1 - _previewEntryExtent);
          final hStart = _previewEntryExtent * bodyH;
          final cardTop = lerpDouble(topStart, 0, expandT)!;
          final cardH = lerpDouble(hStart, screenH, expandT)!;
          final radius = lerpDouble(24, 0, expandT)!;
          final chromeOp = _chromeOpacity();

          return Stack(
            clipBehavior: Clip.none,
            children: [
              // QR zone — ends above bottom nav
              Positioned(
                top: 0,
                left: 0,
                right: 0,
                bottom: navH,
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.center,
                  children: [
                    SizedBox(height: topPad + 50 + 16),
                    QRZone(
                      qrData:  mockQrData,
                      qrScale: _qrScale,
                      onTap:   () => _snapTo(_Pos.peek),
                    ),
                  ],
                ),
              ),

              // Top bar
              Positioned(
                top: topPad,
                left: 0,
                right: 0,
                height: 50,
                child: IgnorePointer(
                  ignoring: _previewCardActive,
                  child: TopBar(slug: mockSlug, onEyeTap: _onEyeTap),
                ),
              ),

              // Bottom nav (same widget as before; lives in stack for z-order)
              Positioned(
                left: 0,
                right: 0,
                bottom: 0,
                height: navH,
                child: IgnorePointer(
                  ignoring: _previewCardActive,
                  child: BottomNav(
                    currentIndex: _navIndex,
                    bottomPad:    botPad,
                    onTap:        (i) => setState(() => _navIndex = i),
                  ),
                ),
              ),

              // Draggable sheet — only while not using the preview morph layer
              if (!_previewCardActive)
                Positioned(
                  top: 0,
                  left: 0,
                  right: 0,
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
                    child:
                        NotificationListener<DraggableScrollableNotification>(
                          onNotification: (n) {
                            setState(() {
                              _sheetExtent = n.extent;
                              _pos = _nearestPos(n.extent);
                            });
                            return false;
                          },
                          child: DraggableScrollableSheet(
                            controller: _sheetController,
                            initialChildSize: kMid,
                            minChildSize: kPeek,
                            maxChildSize: _kTop,
                            snap: false,
                            builder: (context, scrollController) {
                              return NotificationListener<ScrollNotification>(
                                onNotification: (n) {
                                  if (n is ScrollUpdateNotification &&
                                      n.metrics.axis == Axis.vertical) {
                                    _cardScrollPixels = n.metrics.pixels;
                                  }
                                  return false;
                                },
                                child: CardSheet(
                                  scrollController: scrollController,
                                  onHandleTap: () {
                                    if (_pos == _Pos.peek) _snapTo(_Pos.mid);
                                  },
                                  profilePreviewLinksLocked: true,
                                  listTopInset:      0,
                                  displayName:       mockDisplayName,
                                  initials:          mockInitials,
                                  title:             mockTitle,
                                  company:           mockCompany,
                                  viewCount:         mockViewCount,
                                  links:             mockLinks,
                                  hasSensitiveData:  mockHasSensitiveData,
                                  phone:             mockPhone,
                                  email:             mockEmail,
                                ),
                              );
                            },
                          ),
                        ),
                  ),
                ),

              // Floating edit button
              if (!_previewCardActive)
                Positioned(
                  right:  16,
                  bottom: navH + 16,
                  child: EditFab(onTap: () {}),
                ),

              // Profile preview morph + chrome
              if (_previewCardActive)
                Positioned(
                  key: ValueKey(_previewEntryPosition),
                  top: cardTop,
                  left: 0,
                  right: 0,
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
                          child: CardSheet(
                            scrollController: _previewScrollController,
                            onHandleTap: () {},
                            profilePreviewLinksLocked: true,
                            topCornerRadius: radius,
                            listTopInset: PreviewBanner.listTopInset(
                              topInset: mq.padding.top,
                              showSensitiveLine: mockHasSensitiveData,
                            ),
                            // Clear the Save Contact FAB (52px) + its 20px
                            // bottom offset + safe area + a 16px breathing gap.
                            listBottomInset:     mq.padding.bottom + 88,
                            showPremiumSections: false,
                            displayName:         mockDisplayName,
                            initials:            mockInitials,
                            title:               mockTitle,
                            company:             mockCompany,
                            viewCount:           mockViewCount,
                            links:               mockLinks,
                            hasSensitiveData:    mockHasSensitiveData,
                            phone:               mockPhone,
                            email:               mockEmail,
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
                                  top: 0,
                                  left: 0,
                                  right: 0,
                                  child: PreviewBanner(
                                    topInset: mq.padding.top,
                                    horizontalPadding: mq.padding,
                                    background: _previewBannerBg(context),
                                    showSensitiveLine: mockHasSensitiveData,
                                    onBanner:
                                        Theme.of(context).brightness ==
                                            Brightness.dark
                                        ? AppColors.cardText
                                        : Colors.white,
                                    onBannerMuted:
                                        Theme.of(context).brightness ==
                                            Brightness.dark
                                        ? AppColors.cardMuted
                                        : const Color(0xE6FFFFFF),
                                    onClose: _onPreviewClose,
                                  ),
                                ),
                                Positioned(
                                  left:   0,
                                  right:  0,
                                  bottom: mq.padding.bottom + 20,
                                  child: const SaveContactFab(),
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
