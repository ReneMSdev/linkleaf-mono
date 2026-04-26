import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import '../../../core/colors.dart';

class SectionHeader extends StatelessWidget {
  final String              label;
  final bool                showLabel;
  final bool                editMode;
  final VoidCallback        onDelete;
  final VoidCallback        onToggleLabel;
  final ValueChanged<String> onLabelChanged;
  final Widget              child;
  final bool                isFixed;

  const SectionHeader({
    required this.label,
    required this.showLabel,
    required this.editMode,
    required this.onDelete,
    required this.onToggleLabel,
    required this.onLabelChanged,
    required this.child,
    this.isFixed = false,
  });

  @override
  Widget build(BuildContext context) {
    if (!editMode) return child;
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      mainAxisSize: MainAxisSize.min,
      children: [
        _SectionChrome(
          label:          label,
          showLabel:      showLabel,
          isFixed:        isFixed,
          onDelete:       onDelete,
          onToggleLabel:  onToggleLabel,
          onLabelChanged: onLabelChanged,
        ),
        child,
      ],
    );
  }
}

// ── Chrome row ─────────────────────────────────────────────────────────────

class _SectionChrome extends StatefulWidget {
  final String              label;
  final bool                showLabel;
  final bool                isFixed;
  final VoidCallback        onDelete;
  final VoidCallback        onToggleLabel;
  final ValueChanged<String> onLabelChanged;

  const _SectionChrome({
    required this.label,
    required this.showLabel,
    required this.isFixed,
    required this.onDelete,
    required this.onToggleLabel,
    required this.onLabelChanged,
  });

  @override
  State<_SectionChrome> createState() => _SectionChromeState();
}

class _SectionChromeState extends State<_SectionChrome> {
  bool _editing   = false;
  late bool   _showLabel;
  late String _label;
  late final TextEditingController _controller;

  @override
  void initState() {
    super.initState();
    _showLabel = widget.showLabel;
    _label     = widget.label;
    _controller = TextEditingController(text: _label);
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  void _commitEdit() {
    setState(() {
      _editing = false;
      _label   = _controller.text;
    });
    widget.onLabelChanged(_label);
  }

  void _toggleLabel() {
    setState(() => _showLabel = !_showLabel);
    widget.onToggleLabel();
  }

  @override
  Widget build(BuildContext context) {
    final labelStyle = GoogleFonts.plusJakartaSans(
      fontSize:   12,
      fontWeight: FontWeight.w600,
      color:      _showLabel ? AppColors.cardText : AppColors.cardBorder,
    );

    return Container(
      height: 36,
      decoration: const BoxDecoration(
        color: AppColors.cardSub,
        borderRadius: BorderRadius.vertical(top: Radius.circular(12)),
        border: Border(
          top:   BorderSide(color: AppColors.cardBorder),
          left:  BorderSide(color: AppColors.cardBorder),
          right: BorderSide(color: AppColors.cardBorder),
        ),
      ),
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 12),
        child: Row(
          children: [
            // Drag handle — visual only, not wired to reorder yet
            if (!widget.isFixed) ...[
              Opacity(
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
              ),
              const SizedBox(width: 10),
            ],

            // Label — tapping opens inline TextField
            Expanded(
              child: _editing
                  ? TextField(
                      controller: _controller,
                      autofocus:  true,
                      onSubmitted: (_) => _commitEdit(),
                      onTapOutside: (_) => _commitEdit(),
                      style: GoogleFonts.plusJakartaSans(
                        fontSize:   12,
                        fontWeight: FontWeight.w600,
                        color:      AppColors.cardText,
                      ),
                      decoration: const InputDecoration(
                        isDense:        true,
                        contentPadding: EdgeInsets.zero,
                        border:         InputBorder.none,
                      ),
                    )
                  : GestureDetector(
                      onTap: () => setState(() => _editing = true),
                      child: Text(_label, style: labelStyle),
                    ),
            ),

            // Visibility toggle
            GestureDetector(
              onTap:    _toggleLabel,
              behavior: HitTestBehavior.opaque,
              child: Padding(
                padding: const EdgeInsets.all(6),
                child: Icon(
                  _showLabel ? Icons.visibility : Icons.visibility_off,
                  size:  18,
                  color: AppColors.muted,
                ),
              ),
            ),

            // Delete button — hidden for fixed sections
            if (!widget.isFixed)
              GestureDetector(
                onTap:    widget.onDelete,
                behavior: HitTestBehavior.opaque,
                child: const Padding(
                  padding: EdgeInsets.all(6),
                  child: Icon(Icons.close, size: 18, color: AppColors.muted),
                ),
              ),
          ],
        ),
      ),
    );
  }
}
