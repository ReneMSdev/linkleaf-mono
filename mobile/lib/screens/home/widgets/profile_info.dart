import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import '../../../core/colors.dart';

// TODO: replace with provider data
const _mockDisplayName = 'René Villanueva';
const _mockTitle       = 'Product Designer';
const _mockCompany     = 'Salo Labs';
const _mockBio         = 'Building thoughtful digital products. Based in Mexico City.';
const _mockViewCount   = 143;

class ProfileInfo extends StatefulWidget {
  final String  displayName;
  final String  title;
  final String  company;
  final String? bio;
  final int     viewCount;
  final bool    editMode;

  const ProfileInfo({
    this.displayName = _mockDisplayName,
    this.title       = _mockTitle,
    this.company     = _mockCompany,
    this.bio         = _mockBio,
    this.viewCount   = _mockViewCount,
    this.editMode    = false,
  });

  @override
  State<ProfileInfo> createState() => _ProfileInfoState();
}

class _ProfileInfoState extends State<ProfileInfo> {
  String? _activeField;

  late final TextEditingController _nameCtrl;
  late final TextEditingController _titleCtrl;
  late final TextEditingController _companyCtrl;
  late final TextEditingController _bioCtrl;

  @override
  void initState() {
    super.initState();
    _nameCtrl    = TextEditingController(text: widget.displayName);
    _titleCtrl   = TextEditingController(text: widget.title);
    _companyCtrl = TextEditingController(text: widget.company);
    _bioCtrl     = TextEditingController(text: widget.bio ?? '');
  }

  @override
  void dispose() {
    _nameCtrl.dispose();
    _titleCtrl.dispose();
    _companyCtrl.dispose();
    _bioCtrl.dispose();
    super.dispose();
  }

  void _activate(String field) => setState(() => _activeField = field);
  void _deactivate() => setState(() => _activeField = null);

  // ── Bio row (opens overlay rather than inline TextField) ──────────────────

  Widget _bioRow() {
    final labelStyle = GoogleFonts.plusJakartaSans(
      fontSize: 11,
      color:    AppColors.cardMuted,
    );
    final isEmpty = _bioCtrl.text.isEmpty;
    final valueStyle = GoogleFonts.plusJakartaSans(
      fontSize: 13,
      color:    isEmpty ? AppColors.cardBorder : AppColors.cardMuted,
    );

    return Container(
      decoration: _pillDecoration(active: false),
      child: Row(
        children: [
          Expanded(
            child: GestureDetector(
              onTap: () => _activate('bio'),
              child: Padding(
                padding: const EdgeInsets.fromLTRB(14, 11, 0, 11),
                child: Row(
                  children: [
                    SizedBox(
                      width: 56,
                      child: Text('Bio', style: labelStyle),
                    ),
                    Expanded(
                      child: Text(
                        isEmpty ? 'add a bio...' : _bioCtrl.text,
                        style:    valueStyle,
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                      ),
                    ),
                  ],
                ),
              ),
            ),
          ),
          GestureDetector(
            onTap: () => setState(() => _bioCtrl.clear()),
            behavior: HitTestBehavior.opaque,
            child: const Padding(
              padding: EdgeInsets.fromLTRB(8, 11, 14, 11),
              child: _RedClearButton(),
            ),
          ),
        ],
      ),
    );
  }

  // ── Build ─────────────────────────────────────────────────────────────────

  @override
  Widget build(BuildContext context) {
    if (!widget.editMode) return _buildLive();
    return _buildEdit();
  }

  Widget _buildEdit() {
    return Stack(
      children: [
        Padding(
          padding: const EdgeInsets.symmetric(horizontal: 16),
          child: Column(
            children: [
              const SizedBox(height: 8),
              _EditField(
                label:      'Name',
                controller: _nameCtrl,
                active:     _activeField == 'name',
                fontSize:   18,
                fontWeight: FontWeight.w700,
                onTap:      () => _activate('name'),
                onClear:    () => setState(() => _nameCtrl.clear()),
                onDone:     _deactivate,
              ),
              const SizedBox(height: 6),
              _EditField(
                label:      'Title',
                controller: _titleCtrl,
                active:     _activeField == 'title',
                fontSize:   13,
                onTap:      () => _activate('title'),
                onClear:    () => setState(() => _titleCtrl.clear()),
                onDone:     _deactivate,
              ),
              const SizedBox(height: 6),
              _EditField(
                label:      'Company',
                controller: _companyCtrl,
                active:     _activeField == 'company',
                fontSize:   13,
                onTap:      () => _activate('company'),
                onClear:    () => setState(() => _companyCtrl.clear()),
                onDone:     _deactivate,
              ),
              const SizedBox(height: 6),
              _bioRow(),
              const SizedBox(height: 8),
              Text(
                '${widget.viewCount} views',
                style: GoogleFonts.plusJakartaSans(
                  fontSize: 11,
                  color:    const Color(0x998C8070),
                ),
              ),
            ],
          ),
        ),
        if (_activeField == 'bio')
          Positioned.fill(
            child: _BioOverlay(
              controller: _bioCtrl,
              onDone:     _deactivate,
            ),
          ),
      ],
    );
  }

  Widget _buildLive() {
    return Column(
      children: [
        const SizedBox(height: 8),
        Text(
          widget.displayName,
          style: GoogleFonts.plusJakartaSans(
            fontSize:   18,
            fontWeight: FontWeight.w700,
            color:      AppColors.cardText,
            height:     1.1,
          ),
        ),
        const SizedBox(height: 2),
        Text(
          '${widget.title} · ${widget.company}',
          style: GoogleFonts.plusJakartaSans(
            fontSize: 13,
            color:    AppColors.cardMuted,
          ),
        ),
        if (widget.bio != null) ...[
          const SizedBox(height: 2),
          Text(
            widget.bio!,
            style: GoogleFonts.plusJakartaSans(
              fontSize: 13,
              color:    AppColors.cardMuted,
            ),
          ),
        ],
        const SizedBox(height: 4),
        Text(
          '${widget.viewCount} views',
          style: GoogleFonts.plusJakartaSans(
            fontSize: 11,
            color:    const Color(0x998C8070),
          ),
        ),
      ],
    );
  }
}

// ── Shared helpers ─────────────────────────────────────────────────────────

BoxDecoration _pillDecoration({required bool active}) {
  return BoxDecoration(
    color:        AppColors.card,
    borderRadius: BorderRadius.circular(12),
    border: Border.all(
      color: active ? AppColors.cardText : AppColors.cardBorder,
    ),
    boxShadow: const [
      BoxShadow(
        color:      Color(0x0F1A1814),
        blurRadius: 3,
        offset:     Offset(0, 1),
      ),
    ],
  );
}

class _RedClearButton extends StatelessWidget {
  const _RedClearButton();

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

// ── Edit field ─────────────────────────────────────────────────────────────

class _EditField extends StatelessWidget {
  final String                label;
  final TextEditingController controller;
  final bool                  active;
  final double                fontSize;
  final FontWeight            fontWeight;
  final VoidCallback          onTap;
  final VoidCallback          onClear;
  final VoidCallback          onDone;

  const _EditField({
    required this.label,
    required this.controller,
    required this.active,
    required this.onTap,
    required this.onClear,
    required this.onDone,
    this.fontSize   = 14,
    this.fontWeight = FontWeight.w400,
  });

  @override
  Widget build(BuildContext context) {
    final labelStyle = GoogleFonts.plusJakartaSans(
      fontSize: 11,
      color:    AppColors.cardMuted,
    );
    final valueStyle = GoogleFonts.plusJakartaSans(
      fontSize:   fontSize,
      fontWeight: fontWeight,
      color:      AppColors.cardText,
    );

    return Container(
      decoration: _pillDecoration(active: active),
      child: Row(
        children: [
          // Tappable area: label + value / TextField
          Expanded(
            child: GestureDetector(
              onTap: active ? null : onTap,
              child: Padding(
                padding: const EdgeInsets.fromLTRB(14, 11, 0, 11),
                child: Row(
                  children: [
                    SizedBox(
                      width: 56,
                      child: Text(label, style: labelStyle),
                    ),
                    Expanded(
                      child: active
                          ? TextField(
                              controller:  controller,
                              autofocus:   true,
                              maxLines:    1,
                              style:       valueStyle,
                              decoration: const InputDecoration(
                                isDense:        true,
                                contentPadding: EdgeInsets.zero,
                                border:         InputBorder.none,
                              ),
                              onTapOutside: (_) => onDone(),
                              onSubmitted:  (_) => onDone(),
                            )
                          : Text(controller.text, style: valueStyle),
                    ),
                  ],
                ),
              ),
            ),
          ),
          // Clear button
          GestureDetector(
            onTap:    onClear,
            behavior: HitTestBehavior.opaque,
            child: const Padding(
              padding: EdgeInsets.fromLTRB(8, 11, 14, 11),
              child: _RedClearButton(),
            ),
          ),
        ],
      ),
    );
  }
}

// ── Bio overlay ────────────────────────────────────────────────────────────

class _BioOverlay extends StatelessWidget {
  final TextEditingController controller;
  final VoidCallback          onDone;

  const _BioOverlay({required this.controller, required this.onDone});

  @override
  Widget build(BuildContext context) {
    return Container(
      color: AppColors.card,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
            child: Stack(
              alignment: Alignment.center,
              children: [
                Text(
                  'Bio',
                  style: GoogleFonts.plusJakartaSans(
                    fontSize:   15,
                    fontWeight: FontWeight.w600,
                    color:      AppColors.cardText,
                  ),
                ),
                Align(
                  alignment: Alignment.centerRight,
                  child: GestureDetector(
                    onTap: onDone,
                    child: Text(
                      'Done',
                      style: GoogleFonts.plusJakartaSans(
                        fontSize:   15,
                        fontWeight: FontWeight.w600,
                        color:      AppColors.cardText,
                      ),
                    ),
                  ),
                ),
              ],
            ),
          ),
          const Divider(height: 1, thickness: 1, color: AppColors.cardBorder),
          Expanded(
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: TextField(
                controller: controller,
                autofocus:  true,
                maxLines:   null,
                style: GoogleFonts.plusJakartaSans(
                  fontSize: 13,
                  color:    AppColors.cardMuted,
                ),
                decoration: InputDecoration(
                  border:         InputBorder.none,
                  isDense:        true,
                  contentPadding: EdgeInsets.zero,
                  hintText:       'Add a bio...',
                  hintStyle:      GoogleFonts.plusJakartaSans(
                    fontSize: 13,
                    color:    AppColors.cardBorder,
                  ),
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }
}
