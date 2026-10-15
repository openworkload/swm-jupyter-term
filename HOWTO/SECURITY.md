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

## Upload files

Spawn form uploads go through `swmjupyter.upload_paths`:

1. The hub keeps only the file basename.
2. Absolute paths and `..` segments are rejected.
3. The resolved path must stay under the per-spawner upload spool.
4. Optional parent: `SWM_JUPYTER_UPLOAD_ROOT` (container default `/var/lib/swmjupyter/uploads`).

## Hub API token delivery

The JupyterHub server API token is **not** written into the job script body
(`script_content`). The spawner writes it to a mode-`0600` file named
`jupyterhub_api_token` in the upload spool and lists that path in
`#SWM input-files`. On the node, the job script reads the file into
`JUPYTERHUB_API_TOKEN` and removes it.

Hub logs must not contain the raw token. The spawner logs only a length summary
and a redacted script copy.

Sky Port owner checks (swm-core) limit who can show a job when callers use
distinct identities. Hub users that still share one mTLS client certificate
toward swm-core are not fully isolated until per-user certificates are in place.

## Container user and certificates

The image runs as user `jupyterhub` (non-root).

`start-container.sh` mounts only these host files **read-only**:

| Host path | Container path |
|-----------|----------------|
| `~/.swm/cert.pem` | `/home/jupyterhub/.swm/cert.pem` |
| `~/.swm/key.pem` | `/home/jupyterhub/.swm/key.pem` |
| `~/.swm/spool/secure/cluster/ca-chain-cert.pem` | `/home/jupyterhub/.swm/spool/secure/cluster/ca-chain-cert.pem` |
| `~/.swm/jupyter-spawner.conf` (if present) | `/home/jupyterhub/.swm/jupyter-spawner.conf` |

Do not mount the whole `~/.swm` tree as writable data for the hub.

## Related

- Hub-to-node HTTPS and per-user mTLS are separate hardening items.
- Sky Port trust model: swm-core `HOWTO/SECURITY.md`
