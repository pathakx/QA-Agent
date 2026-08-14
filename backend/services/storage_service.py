"""
Supabase Storage Service
=========================
Uploads test artifacts (screenshots, videos) to Supabase Storage
so they persist across Render deployments and are accessible via URL.

Bucket: test-screenshots (public)
Path format: {project_id}/{test_id}/{filename}
"""

import os
import time
from backend.core.supabase_client import supabase

SCREENSHOT_BUCKET = "test-screenshots"


def _ensure_bucket():
    """Create bucket if it doesn't exist (idempotent)."""
    try:
        buckets = supabase.storage.list_buckets()
        existing = [b.name for b in buckets]
        if SCREENSHOT_BUCKET not in existing:
            supabase.storage.create_bucket(
                SCREENSHOT_BUCKET,
                options={"public": True}
            )
            print(f"[STORAGE] Created bucket: {SCREENSHOT_BUCKET}")
    except Exception as e:
        # Bucket may already exist — safe to ignore
        print(f"[STORAGE] Bucket check: {e}")


def upload_screenshot(local_path: str, test_id: str, project_id: str = "default") -> str | None:
    """
    Upload a screenshot file to Supabase Storage.

    Args:
        local_path: Absolute local path to the PNG file
        test_id:    Test case ID (used in storage path)
        project_id: Project ID (used in storage path)

    Returns:
        Public URL of the uploaded file, or None on failure
    """
    if not local_path or not os.path.exists(local_path):
        print(f"[STORAGE] Screenshot file not found: {local_path}")
        return None

    try:
        _ensure_bucket()

        filename = os.path.basename(local_path)
        storage_path = f"{project_id}/{test_id}/{filename}"

        with open(local_path, "rb") as f:
            file_bytes = f.read()

        # Upload to Supabase Storage
        supabase.storage.from_(SCREENSHOT_BUCKET).upload(
            path=storage_path,
            file=file_bytes,
            file_options={"content-type": "image/png", "upsert": "true"}
        )

        # Get public URL
        result = supabase.storage.from_(SCREENSHOT_BUCKET).get_public_url(storage_path)
        print(f"[STORAGE] Screenshot uploaded: {result}")

        # Clean up local file after successful upload
        try:
            os.remove(local_path)
            print(f"[STORAGE] Cleaned up local file: {local_path}")
        except Exception:
            pass

        return result

    except Exception as e:
        print(f"[STORAGE] Upload failed for {local_path}: {e}")
        # Return local path as fallback so result isn't lost
        return local_path


def is_supabase_url(path: str) -> bool:
    """Check if a screenshot path is already a Supabase URL (not a local path)."""
    return path and path.startswith("http")
