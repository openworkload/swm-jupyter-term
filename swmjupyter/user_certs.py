"""Resolve Sky Port mTLS client certs from the hub user's system home."""

from __future__ import annotations

import os
import pwd
import re
from dataclasses import dataclass
from typing import Callable, Optional

# Relative to the system user's home directory.
CERT_REL = ".swm/cert.pem"
KEY_REL = ".swm/key.pem"
CA_REL = ".swm/spool/secure/cluster/ca-chain-cert.pem"

_SAFE_USERNAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._+-]{0,63}$")

Getpwnam = Callable[[str], pwd.struct_passwd]


class UserCertError(ValueError):
    """Hub user has no system account or no usable ~/.swm client certificate."""


@dataclass(frozen=True)
class UserCertPaths:
    cert_file: str
    key_file: str
    ca_file: str
    home_dir: str


def sanitize_cert_username(username: str) -> str:
    """Return a hub username safe to look up as a system account."""
    if not username or "\x00" in username:
        raise UserCertError("Username is empty or contains NUL")
    if "/" in username or "\\" in username or os.sep in username:
        raise UserCertError("Username must not contain path separators")
    if ".." in username or username in {".", ".."}:
        raise UserCertError("Username must not contain '..'")
    if not _SAFE_USERNAME.match(username):
        raise UserCertError(
            "Username may contain only letters, digits, and ._+- "
            "and must start with an alphanumeric character"
        )
    return username


def _require_readable_file(path: str, label: str) -> str:
    if not path:
        raise UserCertError(f"{label} path is empty")
    if not os.path.isfile(path):
        raise UserCertError(f"{label} file not found: {path}")
    if not os.access(path, os.R_OK):
        raise UserCertError(
            f"{label} file is not readable by the hub process: {path} "
            "(grant group/ACL read to the hub user, or run the hub with access to this home)"
        )
    return path


def resolve_user_cert_paths(
    username: str,
    *,
    ca_file: Optional[str] = None,
    getpwnam: Getpwnam = pwd.getpwnam,
) -> UserCertPaths:
    """Map a JupyterHub login name to that system user's ``~/.swm`` client certs.

    The hub login must match a local system account. Certificate material is:

    * ``$HOME/.swm/cert.pem``
    * ``$HOME/.swm/key.pem``
    * ``$HOME/.swm/spool/secure/cluster/ca-chain-cert.pem`` (or ``ca_file`` override)

    Missing system user or missing/unreadable files raise ``UserCertError``
    (job submit / form API must fail closed).
    """
    safe_name = sanitize_cert_username(username)
    try:
        pw = getpwnam(safe_name)
    except KeyError as exc:
        raise UserCertError(
            f"No system user named {safe_name!r}; "
            "create the account and install ~/.swm/cert.pem and key.pem before spawning"
        ) from exc

    home = pw.pw_dir
    if not home or not os.path.isdir(home):
        raise UserCertError(f"System user {safe_name!r} has no usable home directory")

    cert_path = os.path.join(home, CERT_REL)
    key_path = os.path.join(home, KEY_REL)
    if ca_file:
        ca_path = os.path.expanduser(ca_file)
    else:
        ca_path = os.path.join(home, CA_REL)

    return UserCertPaths(
        cert_file=_require_readable_file(cert_path, "Client certificate"),
        key_file=_require_readable_file(key_path, "Client key"),
        ca_file=_require_readable_file(ca_path, "CA"),
        home_dir=home,
    )
