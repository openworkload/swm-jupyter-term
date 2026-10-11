"""Sanitize and contain JupyterHub upload file names."""

from __future__ import annotations

import os
import re


class UploadPathError(ValueError):
    """Client upload name is unsafe or escapes the spool directory."""


# Keep names simple for job scripts and Sky Port input-files.
_SAFE_NAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._+-]{0,254}$")


def safe_upload_basename(filename: str | bytes | None) -> str:
    """Return a single-segment basename safe to join under a spool directory."""
    if filename is None:
        raise UploadPathError("Upload file name is missing")
    if isinstance(filename, bytes):
        try:
            filename = filename.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise UploadPathError("Upload file name is not valid UTF-8") from exc

    raw = str(filename)
    if not raw or "\x00" in raw:
        raise UploadPathError("Upload file name is empty or contains NUL")

    # Reject absolute paths before basename (Unix and Windows-style).
    if os.path.isabs(raw) or raw.startswith(("/", "\\")) or (len(raw) >= 3 and raw[1:3] in (":/", ":\\")):
        raise UploadPathError("Absolute upload paths are not allowed")

    slash_normalized = raw.replace("\\", "/")
    if ".." in slash_normalized.split("/"):
        raise UploadPathError("Upload path must not contain '..' segments")

    normalized = os.path.normpath(slash_normalized)
    if normalized.startswith("..") or normalized == "..":
        raise UploadPathError("Upload path must not contain '..' segments")

    name = os.path.basename(normalized)
    if not name or name in {".", ".."}:
        raise UploadPathError("Upload file name is invalid")
    if name != normalized and os.sep in normalized.replace("\\", "/"):
        # Nested paths are reduced to basename only (no directories under spool).
        pass
    if "/" in name or "\\" in name:
        raise UploadPathError("Upload file name must be a single path segment")
    if not _SAFE_NAME.match(name):
        raise UploadPathError(
            "Upload file name may contain only letters, digits, and ._+- "
            "and must start with an alphanumeric character"
        )
    return name


def resolve_upload_path(spool_dir: str, filename: str | bytes | None) -> str:
    """Resolve a contained destination path under ``spool_dir``."""
    if not spool_dir:
        raise UploadPathError("Upload spool directory is not set")

    os.makedirs(spool_dir, mode=0o700, exist_ok=True)
    base = os.path.realpath(spool_dir)
    name = safe_upload_basename(filename)
    dest = os.path.realpath(os.path.join(base, name))

    try:
        common = os.path.commonpath([base, dest])
    except ValueError as exc:
        raise UploadPathError("Upload path escapes the spool directory") from exc
    if common != base:
        raise UploadPathError("Upload path escapes the spool directory")
    return dest
