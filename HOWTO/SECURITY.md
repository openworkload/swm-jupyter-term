# Security (JupyterHub)

## Authentication

The hub does **not** use open `DummyAuthenticator` by default.

| `SWM_JUPYTER_AUTH` | Authenticator | Notes |
|--------------------|---------------|-------|
| `native` (default) | NativeAuthenticator | Local users with passwords. Signup is closed. |
| `oauth` | GenericOAuthenticator | Set `OAUTH2_CLIENT_ID`, `OAUTH2_CLIENT_SECRET`, `OAUTH2_AUTHORIZE_URL`, `OAUTH2_TOKEN_URL`, `OAUTH2_USERDATA_URL`. |
| `dummy` | DummyAuthenticator | Only with `SWM_JUPYTER_INSECURE_AUTH=1` and a loopback bind. |

Always keep `allow_all` false except the insecure lab mode above.

### Create the first admin (native)

1. Set `SWM_JUPYTER_ADMIN_USER` to the admin login name.
2. Start the hub.
3. Open `http://127.0.0.1:8000` and sign up / set the password for that admin (NativeAuthenticator flow).
4. Create other users as the admin. Do not enable open signup in production.

## Bind address and Docker publish

| Variable | Default | Role |
|----------|---------|------|
| `SWM_JUPYTER_BIND_IP` | `127.0.0.1` | Public proxy listen address |
| `SWM_JUPYTER_BIND_PORT` | `8000` | Public proxy port |
| `SWM_JUPYTER_PUBLISH_ALL` | unset | If `1`, publish on all interfaces (use only behind TLS) |
| `SWM_JUPYTER_HUB_IP` | `0.0.0.0` | Internal hub API for spawners (port 8081) |

`start-container.sh` publishes `127.0.0.1:8000:8000` by default.

## TLS

For production access from other hosts:

1. Prefer a reverse proxy with TLS in front of a loopback-bound hub, or
2. Set `SWM_JUPYTER_SSL_CERT` and `SWM_JUPYTER_SSL_KEY`, and set `SWM_JUPYTER_ENV=production`.

Production mode refuses a non-loopback bind when TLS files are missing.

## Insecure lab mode

Use only on a trusted machine:

```bash
export SWM_JUPYTER_INSECURE_AUTH=1
export SWM_JUPYTER_BIND_IP=127.0.0.1
# optional: export SWM_JUPYTER_AUTH=dummy
```

The hub refuses insecure Dummy auth when the bind is not loopback.

## Related

- Hub-to-node HTTPS and per-user mTLS are separate hardening items.
- Sky Port trust model: swm-core `HOWTO/SECURITY.md`
