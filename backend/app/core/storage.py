"""Google Cloud Storage client and helpers.

All GCS access goes through this module — no other code should import the GCS SDK.
Signed URLs are generated on demand and never persisted.
"""

from __future__ import annotations

import asyncio
import json
import uuid
from datetime import timedelta
from functools import lru_cache

from google.cloud import storage
from google.oauth2 import service_account

from app.config.settings import get_settings


@lru_cache(maxsize=1)
def get_storage_client() -> storage.Client:
    """Returns a cached GCS client initialized from service account credentials.

    Called on first use and cached for the lifetime of the application.
    Uses GCS_SERVICE_ACCOUNT_JSON from settings.
    """
    settings = get_settings()
    credentials_dict = json.loads(settings.GCS_SERVICE_ACCOUNT_JSON.get_secret_value())
    credentials = service_account.Credentials.from_service_account_info(
        credentials_dict,
        scopes=["https://www.googleapis.com/auth/cloud-platform"],
    )
    return storage.Client(
        project=settings.GCS_PROJECT_ID,
        credentials=credentials,
    )


def _upload_sync(
    file_bytes: bytes,
    destination_path: str,
    mime_type: str,
    bucket_name: str,
) -> None:
    client = get_storage_client()
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(destination_path)
    blob.content_type = mime_type
    blob.upload_from_string(file_bytes, content_type=mime_type)


# -----------------------------------------------------------------------------
# Uploads bytes to a GCS bucket at the given destination path.
# Called by media service after receiving confirmed upload metadata.
# Returns the public URL for public bucket or gcs_path for private bucket.
# destination_path format: profiles/{profile_id}/images/{uuid}.jpg
# NOTE: not used in the primary signed URL upload flow.
# Kept for potential server-side operations (file copying, processing).
# -----------------------------------------------------------------------------
async def upload_file(
    file_bytes: bytes,
    destination_path: str,
    mime_type: str,
    bucket_name: str,
) -> str:
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(
        None,
        _upload_sync,
        file_bytes,
        destination_path,
        mime_type,
        bucket_name,
    )
    return destination_path


# -----------------------------------------------------------------------------
# Returns the direct public URL for a file in a public GCS bucket.
# No API call needed — URL is deterministic.
# Only use for public bucket files (images, avatars).
# Never use for private bucket files (resumes).
# -----------------------------------------------------------------------------
def get_public_url(
    gcs_path: str,
    bucket_name: str,
) -> str:
    return f"https://storage.googleapis.com/{bucket_name}/{gcs_path}"


# -----------------------------------------------------------------------------
# Generates a time-limited signed URL for private GCS bucket files.
# Used exclusively for resume downloads — never for public images.
# Default expiry: 60 minutes.
# Runs in threadpool — GCS SDK is synchronous.
# -----------------------------------------------------------------------------
async def get_signed_url(
    gcs_path: str,
    bucket_name: str,
    expiry_minutes: int = 60,
) -> str:
    client = get_storage_client()
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(gcs_path)

    def _sign_sync() -> str:
        return blob.generate_signed_url(
            expiration=timedelta(minutes=expiry_minutes),
            method="GET",
            version="v4",
        )

    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _sign_sync)


# -----------------------------------------------------------------------------
# Generates a signed URL that allows Flutter to upload a file directly to GCS.
# Flutter PUTs the file directly to this URL — FastAPI never handles file bytes.
# Expiry default: 15 minutes — short window to complete the upload.
# Called by media service before returning upload URL to Flutter.
# Runs in threadpool — GCS SDK is synchronous.
# -----------------------------------------------------------------------------
async def generate_signed_upload_url(
    destination_path: str,
    mime_type: str,
    bucket_name: str,
    expiry_minutes: int = 15,
) -> str:
    client = get_storage_client()
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(destination_path)

    def _sign_upload_sync() -> str:
        return blob.generate_signed_url(
            expiration=timedelta(minutes=expiry_minutes),
            method="PUT",
            version="v4",
            content_type=mime_type,
        )

    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _sign_upload_sync)


def _delete_sync(blob: storage.Blob) -> None:
    blob.delete(not_found_ok=True)


# -----------------------------------------------------------------------------
# Deletes a file from GCS. Silent if file does not exist.
# Called by media delete endpoint and background purge job.
# Runs in threadpool — GCS SDK is synchronous.
# -----------------------------------------------------------------------------
async def delete_file(
    gcs_path: str,
    bucket_name: str,
) -> None:
    client = get_storage_client()
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(gcs_path)
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, _delete_sync, blob)


# -----------------------------------------------------------------------------
# Generates a unique GCS object path for a new upload.
# Called before generating a signed upload URL.
# Returns path string — never stored until upload is confirmed.
# -----------------------------------------------------------------------------
def generate_upload_path(
    profile_id: str,
    media_type: str,
    file_extension: str,
) -> str:
    if media_type == "image":
        return f"profiles/{profile_id}/images/{uuid.uuid4()}.{file_extension}"
    if media_type == "resume":
        return f"profiles/{profile_id}/resume.{file_extension}"
    if media_type == "avatar":
        return f"profiles/{profile_id}/avatar.{file_extension}"
    raise ValueError(f"Unsupported media_type for upload path: {media_type!r}")
