"""Resolve JupyterHub auth and public bind settings (fail closed by default)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Optional


class HubSecurityError(ValueError):
    """Invalid or insecure hub security configuration."""


_LOOPBACK = frozenset({"127.0.0.1", "localhost", "::1"})

AUTH_NATIVE = "native"
AUTH_OAUTH = "oauth"
AUTH_DUMMY = "dummy"

AUTHENTICATOR_NATIVE = "nativeauthenticator.NativeAuthenticator"
AUTHENTICATOR_OAUTH = "oauthenticator.generic.GenericOAuthenticator"
AUTHENTICATOR_DUMMY = "dummy"


@dataclass(frozen=True)
class HubSecuritySettings:
    authenticator_class: str
    allow_all: bool
    bind_ip: str
    bind_port: int
    open_signup: bool
    admin_users: frozenset[str]
    insecure_auth: bool
    require_tls: bool
    ssl_cert: str
    ssl_key: str
    internal_ssl: bool
    trusted_alt_names: tuple[str, ...]
    oauth_client_id: str
    oauth_client_secret: str
    oauth_authorize_url: str
    oauth_token_url: str
    oauth_userdata_url: str


def _truthy(value: Optional[str]) -> bool:
    if value is None:
        return False
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _falsy(value: Optional[str]) -> bool:
    if value is None:
        return False
    return value.strip().lower() in {"0", "false", "no", "off"}


def _is_loopback(bind_ip: str) -> bool:
    return bind_ip.strip().lower() in _LOOPBACK


def docker_publish_arg(bind_ip: str, port: int) -> str:
    """Return a Docker ``--publish`` value for the public hub UI port."""
    if _is_loopback(bind_ip):
        return f"127.0.0.1:{port}:{port}"
    return f"{port}:{port}"


def resolve_internal_ssl(env: Mapping[str, str], bind_ip: str) -> bool:
    """Whether hub↔singleuser internal SSL is enabled.

    Default is on. ``SWM_JUPYTER_INTERNAL_SSL=0`` is allowed only on a loopback
    bind (lab). Non-loopback plain HTTP is refused.
    """
    raw = env.get("SWM_JUPYTER_INTERNAL_SSL")
    if raw is None or not str(raw).strip():
        return True
    if _truthy(raw):
        return True
    if _falsy(raw):
        if not _is_loopback(bind_ip):
            raise HubSecurityError(
                "SWM_JUPYTER_INTERNAL_SSL=0 is only allowed when SWM_JUPYTER_BIND_IP is loopback"
            )
        return False
    raise HubSecurityError(f"Invalid SWM_JUPYTER_INTERNAL_SSL={raw!r}; use 1/0 or true/false")


def resolve_trusted_alt_names(env: Mapping[str, str]) -> tuple[str, ...]:
    """DNS/IP SANs for the hub internal certificate (remote singleuser verify)."""
    names: list[str] = ["DNS:localhost", "IP:127.0.0.1"]
    host = (env.get("SWM_JUPYTER_HUB_CONNECT_HOST") or env.get("SWM_JUPYTER_HUB_HOSTNAME") or "").strip()
    if not host:
        # Spawner default host name used in job scripts when conf omits jupyterhub_host.
        host = "localhost"
    if host.lower() not in {"localhost", "127.0.0.1", "::1"}:
        names.append(f"DNS:{host}")
    extra = (env.get("SWM_JUPYTER_TRUSTED_ALT_NAMES") or "").strip()
    if extra:
        for part in extra.split(","):
            item = part.strip()
            if item and item not in names:
                names.append(item)
    return tuple(names)


def resolve_hub_security(env: Optional[Mapping[str, str]] = None) -> HubSecuritySettings:
    """Build hub security settings from environment variables.

    Environment:
      SWM_JUPYTER_AUTH: native (default) | oauth | dummy
      SWM_JUPYTER_INSECURE_AUTH: allow dummy only with loopback bind
      SWM_JUPYTER_BIND_IP: public proxy bind (default 127.0.0.1)
      SWM_JUPYTER_BIND_PORT: public proxy port (default 8000)
      SWM_JUPYTER_PUBLISH_ALL: if truthy, bind_ip becomes 0.0.0.0 unless BIND_IP set
      SWM_JUPYTER_ADMIN_USER: optional admin username for NativeAuthenticator
      SWM_JUPYTER_ENV: production triggers TLS requirement when not on loopback
      SWM_JUPYTER_SSL_CERT / SWM_JUPYTER_SSL_KEY: optional TLS material for the hub
      SWM_JUPYTER_INTERNAL_SSL: hub↔node mTLS (default on; 0 only on loopback)
      SWM_JUPYTER_HUB_CONNECT_HOST: hostname singleusers use to reach the hub API
      SWM_JUPYTER_TRUSTED_ALT_NAMES: extra comma-separated SANs (DNS:… / IP:…)
      OAUTH2_CLIENT_ID / OAUTH2_CLIENT_SECRET / OAUTH2_AUTHORIZE_URL /
      OAUTH2_TOKEN_URL / OAUTH2_USERDATA_URL: required when AUTH=oauth
    """
    env = env if env is not None else {}

    bind_port_raw = (env.get("SWM_JUPYTER_BIND_PORT") or "8000").strip()
    try:
        bind_port = int(bind_port_raw)
    except ValueError as exc:
        raise HubSecurityError(f"Invalid SWM_JUPYTER_BIND_PORT: {bind_port_raw}") from exc
    if bind_port < 1 or bind_port > 65535:
        raise HubSecurityError(f"Invalid SWM_JUPYTER_BIND_PORT: {bind_port}")

    bind_ip = (env.get("SWM_JUPYTER_BIND_IP") or "").strip()
    if not bind_ip:
        if _truthy(env.get("SWM_JUPYTER_PUBLISH_ALL")):
            bind_ip = "0.0.0.0"  # nosec B104
        else:
            bind_ip = "127.0.0.1"

    insecure_auth = _truthy(env.get("SWM_JUPYTER_INSECURE_AUTH"))
    auth_mode = (env.get("SWM_JUPYTER_AUTH") or AUTH_NATIVE).strip().lower()
    if insecure_auth and auth_mode == AUTH_NATIVE and not (env.get("SWM_JUPYTER_AUTH") or "").strip():
        # Explicit insecure without AUTH defaults to dummy for local demos.
        auth_mode = AUTH_DUMMY

    ssl_cert = (env.get("SWM_JUPYTER_SSL_CERT") or "").strip()
    ssl_key = (env.get("SWM_JUPYTER_SSL_KEY") or "").strip()
    production = (env.get("SWM_JUPYTER_ENV") or "").strip().lower() == "production"
    require_tls = production and not _is_loopback(bind_ip)
    internal_ssl = resolve_internal_ssl(env, bind_ip)
    trusted_alt_names = resolve_trusted_alt_names(env)

    if require_tls and (not ssl_cert or not ssl_key):
        raise HubSecurityError(
            "Production non-loopback bind requires SWM_JUPYTER_SSL_CERT and SWM_JUPYTER_SSL_KEY "
            "(or bind to 127.0.0.1 behind a TLS reverse proxy)"
        )

    admin_raw = (env.get("SWM_JUPYTER_ADMIN_USER") or "").strip()
    admin_users = frozenset([admin_raw]) if admin_raw else frozenset()

    if auth_mode == AUTH_DUMMY:
        if not insecure_auth:
            raise HubSecurityError("DummyAuthenticator requires SWM_JUPYTER_INSECURE_AUTH=1 and a loopback bind")
        if not _is_loopback(bind_ip):
            raise HubSecurityError("Insecure DummyAuthenticator is only allowed when SWM_JUPYTER_BIND_IP is loopback")
        return HubSecuritySettings(
            authenticator_class=AUTHENTICATOR_DUMMY,
            allow_all=True,
            bind_ip=bind_ip,
            bind_port=bind_port,
            open_signup=False,
            admin_users=admin_users,
            insecure_auth=True,
            require_tls=False,
            ssl_cert=ssl_cert,
            ssl_key=ssl_key,
            internal_ssl=internal_ssl,
            trusted_alt_names=trusted_alt_names,
            oauth_client_id="",
            oauth_client_secret="",  # nosec B106
            oauth_authorize_url="",
            oauth_token_url="",
            oauth_userdata_url="",
        )

    if auth_mode == AUTH_OAUTH:
        oauth_client_id = (env.get("OAUTH2_CLIENT_ID") or "").strip()
        oauth_client_secret = (env.get("OAUTH2_CLIENT_SECRET") or "").strip()
        oauth_authorize_url = (env.get("OAUTH2_AUTHORIZE_URL") or "").strip()
        oauth_token_url = (env.get("OAUTH2_TOKEN_URL") or "").strip()
        oauth_userdata_url = (env.get("OAUTH2_USERDATA_URL") or "").strip()
        missing = [
            name
            for name, value in (
                ("OAUTH2_CLIENT_ID", oauth_client_id),
                ("OAUTH2_CLIENT_SECRET", oauth_client_secret),
                ("OAUTH2_AUTHORIZE_URL", oauth_authorize_url),
                ("OAUTH2_TOKEN_URL", oauth_token_url),
                ("OAUTH2_USERDATA_URL", oauth_userdata_url),
            )
            if not value
        ]
        if missing:
            raise HubSecurityError("OAuth auth requires env vars: " + ", ".join(missing))
        return HubSecuritySettings(
            authenticator_class=AUTHENTICATOR_OAUTH,
            allow_all=False,
            bind_ip=bind_ip,
            bind_port=bind_port,
            open_signup=False,
            admin_users=admin_users,
            insecure_auth=False,
            require_tls=require_tls,
            ssl_cert=ssl_cert,
            ssl_key=ssl_key,
            internal_ssl=internal_ssl,
            trusted_alt_names=trusted_alt_names,
            oauth_client_id=oauth_client_id,
            oauth_client_secret=oauth_client_secret,
            oauth_authorize_url=oauth_authorize_url,
            oauth_token_url=oauth_token_url,
            oauth_userdata_url=oauth_userdata_url,
        )

    if auth_mode != AUTH_NATIVE:
        raise HubSecurityError(f"Unknown SWM_JUPYTER_AUTH={auth_mode!r}; use native, oauth, or dummy")

    return HubSecuritySettings(
        authenticator_class=AUTHENTICATOR_NATIVE,
        allow_all=False,
        bind_ip=bind_ip,
        bind_port=bind_port,
        open_signup=False,
        admin_users=admin_users,
        insecure_auth=False,
        require_tls=require_tls,
        ssl_cert=ssl_cert,
        ssl_key=ssl_key,
        internal_ssl=internal_ssl,
        trusted_alt_names=trusted_alt_names,
        oauth_client_id="",
        oauth_client_secret="",  # nosec B106
        oauth_authorize_url="",
        oauth_token_url="",
        oauth_userdata_url="",
    )


def bind_url(settings: HubSecuritySettings) -> str:
    scheme = "https" if settings.ssl_cert and settings.ssl_key else "http"
    return f"{scheme}://{settings.bind_ip}:{settings.bind_port}"
