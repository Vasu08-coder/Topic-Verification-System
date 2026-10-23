from __future__ import annotations

import os
import re
from typing import BinaryIO

from app.core.exceptions import ValidationException


def validate_file_signature(file_bytes: bytes | bytearray | memoryview, expected_type: str) -> bool:
    """Validate the file signature for a supported upload type."""
    if not isinstance(file_bytes, (bytes, bytearray, memoryview)):
        return False

    data = bytes(file_bytes)
    if not data:
        return False

    if expected_type == "pdf":
        return data.startswith(b"%PDF")

    if expected_type in {"docx", "xlsx"}:
        return data.startswith(b"PK\x03\x04")

    return False


def enforce_max_size(file_obj: BinaryIO, max_bytes: int) -> None:
    """Reject oversized uploads before fully loading their contents into memory."""
    if max_bytes <= 0:
        raise ValidationException("File exceeds the maximum allowed size")

    if not hasattr(file_obj, "seek") or not hasattr(file_obj, "tell"):
        raise ValidationException("File stream is not seekable")

    current_position = file_obj.tell()
    try:
        file_obj.seek(0, os.SEEK_END)
        size = file_obj.tell()
    finally:
        file_obj.seek(current_position)

    if size > max_bytes:
        raise ValidationException("File exceeds the maximum allowed size")


def sanitize_filename(filename: str | None) -> str:
    """Remove path traversal and unsafe characters from user-supplied filenames."""
    if not filename:
        return "uploaded_file"

    normalized = filename.strip().replace("\\", "/")
    normalized = normalized.replace("../", "").replace("./", "")
    normalized = normalized.replace("/", "")
    normalized = re.sub(r"[^A-Za-z0-9._-]", "_", normalized)
    normalized = normalized.strip("._-")
    return normalized or "uploaded_file"
