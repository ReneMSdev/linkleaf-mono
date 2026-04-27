// ignore_for_file: unused_element
import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import '../../../core/colors.dart';
import '../../../models/link.dart';

// TODO: replace with provider data
const _mockLink = Link(id: '1', title: 'Portfolio', url: 'https://portfolio.example.com');

class LinkPill extends StatefulWidget {
  final Link link;
  final bool linkPreviewLocked;
  final bool editMode;

  const LinkPill({
    required this.link,
    this.linkPreviewLocked = false,
    this.editMode          = false,
  });

  @override
  State<LinkPill> createState() => _LinkPillState();
}

class _LinkPillState extends State<LinkPill> {
  bool _expanded = false;
  late final TextEditingController _titleCtrl;
  late final TextEditingController _urlCtrl;

  Color get _iconBg {
    switch (widget.link.title.toLowerCase()) {
      case 'portfolio': return const Color(0xFFFF6B35);
      case 'github':    return const Color(0xFF1A1814);
      case 'linkedin':  return const Color(0xFF0A66C2);
      case 'dribbble':  return const Color(0xFFEA4C89);
      default:          return AppColors.muted;
    }
  }

  @override
  void initState() {
    super.initState();
    _titleCtrl = TextEditingController(text: widget.link.title);
    _urlCtrl   = TextEditingController(text: widget.link.url);
  }

  @override
  void dispose() {
    _titleCtrl.dispose();
    _urlCtrl.dispose();
    super.dispose();
  }

  // ── Shared ──────────────────────────────────────────────────────────────────

  Widget _iconBadge() => Container(
        width:  24,
        height: 24,
        decoration: BoxDecoration(
          color:        _iconBg,
          borderRadius: BorderRadius.circular(6),
        ),
        child: Center(
          child: Container(
            width:  10,
            height: 10,
            decoration: BoxDecoration(
              color:        const Color(0xE5FFFFFF),
              borderRadius: BorderRadius.circular(2),
            ),
          ),
        ),
      );

  Widget _dragGrip() => Opacity(
        opacity: 0.35,
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Container(width: 14, height: 1.5, color: AppColors.cardText),
            const SizedBox(height: 3),
            Container(width: 14, height: 1.5, color: AppColors.cardText),
            const SizedBox(height: 3),
            Container(width: 14, height: 1.5, color: AppColors.cardText),
          ],
        ),
      );

  // ── Edit mode ───────────────────────────────────────────────────────────────

  Widget _editField({
    required String label,
    required TextEditingController controller,
  }) {
    return Container(
      decoration: BoxDecoration(
        color:        AppColors.cardSub,
        borderRadius: BorderRadius.circular(10),
        border:       Border.all(color: AppColors.cardBorder),
      ),
      child: Padding(
        padding: const EdgeInsets.fromLTRB(12, 8, 12, 8),
        child: Row(
          children: [
            SizedBox(
              width: 56,
              child: Text(
                label,
                style: GoogleFonts.plusJakartaSans(
                  fontSize: 11,
                  color:    AppColors.cardMuted,
                ),
              ),
            ),
            Expanded(
              child: TextField(
                controller: controller,
                style: GoogleFonts.plusJakartaSans(
                  fontSize: 13,
                  color:    AppColors.cardText,
                ),
                decoration: const InputDecoration(
                  isDense:        true,
                  contentPadding: EdgeInsets.zero,
                  border:         InputBorder.none,
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildEdit() {
    return Container(
      decoration: BoxDecoration(
        color:        AppColors.card,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(
          color: _expanded ? const Color(0x661A1814) : AppColors.cardBorder,
        ),
        boxShadow: const [
          BoxShadow(color: Color(0x0F1A1814), blurRadius: 3, offset: Offset(0, 1)),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          // Header row — tap to toggle expand (except on ✕)
          GestureDetector(
            onTap:    () => setState(() => _expanded = !_expanded),
            behavior: HitTestBehavior.opaque,
            child: Padding(
              padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 11),
              child: Row(
                children: [
                  _dragGrip(),
                  const SizedBox(width: 10),
                  _iconBadge(),
                  const SizedBox(width: 10),
                  Expanded(
                    child: ValueListenableBuilder<TextEditingValue>(
                      valueListenable: _titleCtrl,
                      builder: (_, val, __) => Text(
                        val.text.isEmpty ? widget.link.title : val.text,
                        style: GoogleFonts.plusJakartaSans(
                          fontSize:   14,
                          fontWeight: FontWeight.w500,
                          color:      AppColors.cardText,
                        ),
                      ),
                    ),
                  ),
                  GestureDetector(
                    onTap:    () {},
                    behavior: HitTestBehavior.opaque,
                    child: const Padding(
                      padding: EdgeInsets.only(left: 8),
                      child: _RedX(),
                    ),
                  ),
                ],
              ),
            ),
          ),
          if (_expanded) ...[
            const Divider(height: 1, thickness: 1, color: AppColors.cardBorder),
            Padding(
              padding: const EdgeInsets.fromLTRB(12, 8, 12, 12),
              child: Column(
                children: [
                  _editField(label: 'Title', controller: _titleCtrl),
                  const SizedBox(height: 6),
                  _editField(label: 'URL',   controller: _urlCtrl),
                ],
              ),
            ),
          ],
        ],
      ),
    );
  }

  // ── Live mode ───────────────────────────────────────────────────────────────

  @override
  Widget build(BuildContext context) {
    if (widget.editMode) return _buildEdit();

    final content = Container(
      decoration: BoxDecoration(
        color:        AppColors.card,
        border:       Border.all(color: AppColors.cardBorder),
        borderRadius: BorderRadius.circular(12),
        boxShadow: const [
          BoxShadow(color: Color(0x0F1A1814), blurRadius: 3, offset: Offset(0, 1)),
        ],
      ),
      child: Material(
        color: Colors.transparent,
        child: InkWell(
          borderRadius: BorderRadius.circular(12),
          onTap: widget.linkPreviewLocked ? null : () {},
          child: Padding(
            padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 11),
            child: Row(
              children: [
                _iconBadge(),
                const SizedBox(width: 10),
                Expanded(
                  child: Text(
                    widget.link.title,
                    style: GoogleFonts.plusJakartaSans(
                      fontSize:   14,
                      fontWeight: FontWeight.w500,
                      color:      AppColors.cardText,
                    ),
                  ),
                ),
                const Icon(Icons.chevron_right, size: 16, color: Color(0x4D1A1814)),
              ],
            ),
          ),
        ),
      ),
    );
    if (!widget.linkPreviewLocked) return content;
    return IgnorePointer(child: content);
  }
}

// ── Red X button (matches profile_info _RedClearButton style) ─────────────

class _RedX extends StatelessWidget {
  const _RedX();

  @override
  Widget build(BuildContext context) {
    return Container(
      width:  20,
      height: 20,
      decoration: BoxDecoration(
        color: const Color(0xFFFEF2F2),
        shape: BoxShape.circle,
        border: Border.all(color: const Color(0xFFF87171), width: 1.0),
      ),
      child: const Icon(
        Icons.close,
        size:  13,
        color: Color(0xFFEF4444),
        shadows: [Shadow(color: Color(0xFFEF4444), blurRadius: 1.0)],
      ),
    );
  }
}
