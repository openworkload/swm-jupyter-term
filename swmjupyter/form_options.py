"""Sanitize spawn-form values that are interpolated into #SWM job directives."""

from __future__ import annotations

import re


class FormOptionError(ValueError):
    """Client spawn-form value is missing or unsafe for a #SWM directive."""


_FLAVOR = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
_GPUS = re.compile(r"^[0-9]{1,4}$")
_CLOUD_IMAGE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._/-]{0,200}$")
_WHITESPACE = re.compile(r"\s")


def _decode_form_value(raw: str | bytes | None, field: str) -> str:
    if raw is None:
        raise FormOptionError(f"{field} is missing")
    if isinstance(raw, bytes):
        try:
            raw = raw.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise FormOptionError(f"{field} is not valid UTF-8") from exc
    if not isinstance(raw, str):
        raise FormOptionError(f"{field} must be a string")
    if not raw:
        raise FormOptionError(f"{field} is empty")
    if "\x00" in raw:
        raise FormOptionError(f"{field} contains NUL")
    if "\n" in raw or "\r" in raw:
        raise FormOptionError(f"{field} must not contain newlines")
    if _WHITESPACE.search(raw):
        raise FormOptionError(f"{field} must not contain whitespace")
    if "#swm" in raw.lower():
        raise FormOptionError(f"{field} must not contain #SWM")
    return raw


def swm_directive_token(value: str | bytes | None) -> str:
    """Reject values that could break out of a single #SWM directive line."""
    return _decode_form_value(value, "swm_token")


def sanitize_flavor(raw: str | bytes | None) -> str:
    value = _decode_form_value(raw, "flavor")
    if not _FLAVOR.match(value):
        raise FormOptionError(
            "flavor may contain only letters, digits, and ._- and must start with an alphanumeric character"
        )
    return value


def sanitize_gpus(raw: str | bytes | None) -> str:
    value = _decode_form_value(raw, "gpus")
    if not _GPUS.match(value):
        raise FormOptionError("gpus must be a non-negative integer of at most 4 digits")
    return value


def sanitize_cloud_image(raw: str | bytes | None) -> str:
    value = _decode_form_value(raw, "cloud-image")
    if not _CLOUD_IMAGE.match(value):
        raise FormOptionError(
            "cloud-image may contain only letters, digits, and ._/- "
            "and must start with an alphanumeric character"
        )
    return value
