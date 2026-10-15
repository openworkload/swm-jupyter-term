import os
import sys

sys.path.append(os.path.dirname(os.path.realpath(__file__)))

from swmjupyter.hub_security import (  # noqa: E402
    AUTHENTICATOR_DUMMY,
    AUTHENTICATOR_NATIVE,
    AUTHENTICATOR_OAUTH,
    HubSecurityError,
    bind_url,
    resolve_hub_security,
)
from swmjupyter.spawner import SwmSpawner  # noqa: E402

try:
    _security = resolve_hub_security(os.environ)
except HubSecurityError as exc:
    raise SystemExit(f"JupyterHub security configuration error: {exc}") from exc

c.JupyterHub.bind_url = bind_url(_security)
c.JupyterHub.hub_ip = os.environ.get("SWM_JUPYTER_HUB_IP", "0.0.0.0")
c.JupyterHub.hub_port = int(os.environ.get("SWM_JUPYTER_HUB_PORT", "8081"))
c.JupyterHub.log_level = os.environ.get("SWM_JUPYTER_LOG_LEVEL", "INFO")
c.JupyterHub.spawner_class = "swmjupyter.spawner.SwmSpawner"

c.JupyterHub.authenticator_class = _security.authenticator_class
c.Authenticator.allow_all = _security.allow_all
if _security.admin_users:
    c.Authenticator.admin_users = set(_security.admin_users)

if _security.authenticator_class == AUTHENTICATOR_NATIVE:
    c.NativeAuthenticator.open_signup = _security.open_signup

if _security.authenticator_class == AUTHENTICATOR_OAUTH:
    c.GenericOAuthenticator.client_id = _security.oauth_client_id
    c.GenericOAuthenticator.client_secret = _security.oauth_client_secret
    c.GenericOAuthenticator.authorize_url = _security.oauth_authorize_url
    c.GenericOAuthenticator.token_url = _security.oauth_token_url
    c.GenericOAuthenticator.userdata_url = _security.oauth_userdata_url
    c.GenericOAuthenticator.allow_all = False

if _security.ssl_cert and _security.ssl_key:
    c.JupyterHub.ssl_cert = _security.ssl_cert
    c.JupyterHub.ssl_key = _security.ssl_key

if _security.insecure_auth and _security.authenticator_class == AUTHENTICATOR_DUMMY:
    # Local demos only; resolve_hub_security already enforced loopback bind.
    pass

c.JupyterHub.oauth_token_expires_in = 3600
c.JupyterHub.tornado_settings = {"slow_spawn_timeout": 0}

# mTLS client identity: hub login name must match a system user; certs are
# <that-user-home>/.swm/{cert,key}.pem (see swmjupyter.user_certs).
# Optional shared CA override:
# c.SwmSpawner._swm_ca_file = "/path/to/ca-chain-cert.pem"
c.SwmSpawner.start_timeout = 1800
c.SwmSpawner.http_timeout = 60
c.SwmSpawner.debug = os.environ.get("SWM_JUPYTER_SPAWNER_DEBUG", "").lower() in {
    "1",
    "true",
    "yes",
}
