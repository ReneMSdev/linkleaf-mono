"""Pillow-based image processing and MIME validation for media uploads."""

from __future__ import annotations

import io

import magic
from PIL import Image

from app.core.exceptions import ValidationError
from app.core.types import SUPPORTED_DOCUMENT_TYPES, SUPPORTED_IMAGE_TYPES

AVATAR_SIZE = (512, 512)
PROFILE_IMAGE_MAX_WIDTH = 1200
PROFILE_IMAGE_MAX_HEIGHT = 1200
WEBP_QUALITY = 85
MAX_IMAGE_SIZE_BYTES = 10 * 1024 * 1024  # 10MB
MAX_RESUME_SIZE_BYTES = 5 * 1024 * 1024  # 5MB


# -----------------------------------------------------------------------------
# Validates file bytes against expected MIME types using python-magic.
# Uses actual file bytes — not filename or Content-Type header — for security.
# Returns detected mime type string.
# Raises ValidationError if mime type not in expected_types.
# -----------------------------------------------------------------------------
def validate_mime_type(
    file_bytes: bytes,
    expected_types: frozenset[str],
) -> str:
    detected = magic.from_buffer(file_bytes, mime=True)
    if detected not in expected_types:
        raise ValidationError(
            f"Invalid file type: {detected}. "
            f"Allowed types: {', '.join(sorted(expected_types))}"
        )
    return detected


# -----------------------------------------------------------------------------
# Processes an avatar image upload.
# Flutter pre-crops to square before upload — backend resizes to 512×512 WebP.
# Validates mime type is a supported image type.
# Returns processed WebP bytes.
# Raises ValidationError on invalid mime type or oversized file.
# -----------------------------------------------------------------------------
def process_avatar(image_bytes: bytes) -> bytes:
    if len(image_bytes) > MAX_IMAGE_SIZE_BYTES:
        raise ValidationError(
            f"Avatar file too large. Maximum size is {MAX_IMAGE_SIZE_BYTES // (1024 * 1024)}MB."
        )
    validate_mime_type(image_bytes, SUPPORTED_IMAGE_TYPES)

    with Image.open(io.BytesIO(image_bytes)) as img:
        img = img.convert("RGBA")
        img = img.resize(AVATAR_SIZE, Image.LANCZOS)
        output = io.BytesIO()
        img.save(output, format="WEBP", quality=WEBP_QUALITY)
        return output.getvalue()


# -----------------------------------------------------------------------------
# Processes a profile image upload.
# Resizes to max 1200×1200 preserving aspect ratio, converts to WebP.
# Validates mime type is a supported image type.
# Returns processed WebP bytes.
# Raises ValidationError on invalid mime type or oversized file.
# -----------------------------------------------------------------------------
def process_profile_image(image_bytes: bytes) -> bytes:
    if len(image_bytes) > MAX_IMAGE_SIZE_BYTES:
        raise ValidationError(
            f"Image file too large. Maximum size is {MAX_IMAGE_SIZE_BYTES // (1024 * 1024)}MB."
        )
    validate_mime_type(image_bytes, SUPPORTED_IMAGE_TYPES)

    with Image.open(io.BytesIO(image_bytes)) as img:
        img = img.convert("RGBA")
        img.thumbnail(
            (PROFILE_IMAGE_MAX_WIDTH, PROFILE_IMAGE_MAX_HEIGHT),
            Image.LANCZOS,
        )
        output = io.BytesIO()
        img.save(output, format="WEBP", quality=WEBP_QUALITY)
        return output.getvalue()


# -----------------------------------------------------------------------------
# Validates a resume upload — PDF or Word documents only.
# No processing — resume stored as-is in private GCS bucket.
# Returns detected mime type.
# Raises ValidationError on invalid mime type or oversized file.
# -----------------------------------------------------------------------------
def validate_resume(file_bytes: bytes) -> str:
    if len(file_bytes) > MAX_RESUME_SIZE_BYTES:
        raise ValidationError(
            f"Resume file too large. Maximum size is {MAX_RESUME_SIZE_BYTES // (1024 * 1024)}MB."
        )
    return validate_mime_type(file_bytes, SUPPORTED_DOCUMENT_TYPES)
