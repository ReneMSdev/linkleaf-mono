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

  // ── Field builders ────────────────────────────────────────────────────────

  Widget _tappable({
    required String field,
    required Widget child,
  }) {
    return GestureDetector(
      onTap: () => _activate(field),
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
        decoration: BoxDecoration(
          color:        AppColors.cardSub,
          borderRadius: BorderRadius.circular(8),
          border:       Border.all(color: AppColors.cardBorder),
        ),
        child: child,
      ),
    );
  }

  Widget _activeTextField({
    required TextEditingController controller,
    required TextStyle style,
    int maxLines = 1,
  }) {
    return TextField(
      controller:  controller,
      autofocus:   true,
      maxLines:    maxLines,
      style:       style,
      decoration: InputDecoration(
        filled:         true,
        fillColor:      AppColors.surface,
        isDense:        true,
        contentPadding: const EdgeInsets.symmetric(horizontal: 8, vertical: 6),
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(8),
          borderSide:   const BorderSide(color: AppColors.cardText),
        ),
        enabledBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(8),
          borderSide:   const BorderSide(color: AppColors.cardText),
        ),
        focusedBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(8),
          borderSide:   const BorderSide(color: AppColors.cardText),
        ),
      ),
      onTapOutside: (_) => _deactivate(),
      onSubmitted:  (_) => _deactivate(),
    );
  }

  Widget _nameField() {
    final style = GoogleFonts.plusJakartaSans(
      fontSize:   18,
      fontWeight: FontWeight.w700,
      color:      AppColors.cardText,
      height:     1.1,
    );
    if (_activeField == 'name') {
      return _activeTextField(controller: _nameCtrl, style: style);
    }
    return _tappable(
      field: 'name',
      child: Text(widget.displayName, style: style),
    );
  }

  Widget _titleField() {
    final style = GoogleFonts.plusJakartaSans(
      fontSize: 13,
      color:    AppColors.cardMuted,
    );
    if (_activeField == 'title') {
      return _activeTextField(controller: _titleCtrl, style: style);
    }
    return _tappable(
      field: 'title',
      child: Text(widget.title, style: style),
    );
  }

  Widget _companyField() {
    final style = GoogleFonts.plusJakartaSans(
      fontSize: 13,
      color:    AppColors.cardMuted,
    );
    if (_activeField == 'company') {
      return _activeTextField(controller: _companyCtrl, style: style);
    }
    return _tappable(
      field: 'company',
      child: Text(widget.company, style: style),
    );
  }

  Widget _bioField() {
    final style = GoogleFonts.plusJakartaSans(
      fontSize: 13,
      color:    AppColors.cardMuted,
    );
    if (_activeField == 'bio') {
      return _activeTextField(controller: _bioCtrl, style: style, maxLines: 3);
    }
    if (widget.bio == null) {
      return GestureDetector(
        onTap: () => _activate('bio'),
        child: Container(
          width:   double.infinity,
          padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
          decoration: BoxDecoration(
            color:        AppColors.cardSub,
            borderRadius: BorderRadius.circular(8),
            border:       Border.all(color: AppColors.cardBorder),
          ),
          child: Text(
            'add a bio...',
            style: GoogleFonts.plusJakartaSans(
              fontSize: 13,
              color:    AppColors.cardBorder,
            ),
          ),
        ),
      );
    }
    return _tappable(
      field: 'bio',
      child: Text(widget.bio!, style: style),
    );
  }

  // ── Build ─────────────────────────────────────────────────────────────────

  @override
  Widget build(BuildContext context) {
    if (!widget.editMode) return _buildLive();

    return Column(
      children: [
        const SizedBox(height: 8),
        _nameField(),
        const SizedBox(height: 4),
        _titleField(),
        const SizedBox(height: 4),
        _companyField(),
        const SizedBox(height: 4),
        _bioField(),
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
