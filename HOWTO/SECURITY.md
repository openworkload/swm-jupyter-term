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
2. Ensure a **system account** with that same name exists (see per-user mTLS below).
3. Start the hub.
4. Open `http://127.0.0.1:8000` and sign up / set the password for that admin (NativeAuthenticator flow).
5. Create other users as the admin. Do not enable open signup in production.
6. Each hub login must also exist as a system user with Sky Port client certs installed.

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

## Hub-to-node HTTPS (internal SSL)

Traffic between the hub and single-user servers uses JupyterHub **internal SSL**
(mutual TLS) by default.

| Variable | Default | Role |
|----------|---------|------|
| `SWM_JUPYTER_INTERNAL_SSL` | on | Set to `0` only on a loopback bind (lab HTTP) |
| `SWM_JUPYTER_HUB_CONNECT_HOST` | `localhost` | Hostname singleusers use in `JUPYTERHUB_API_URL` (added as hub cert SAN) |
| `SWM_JUPYTER_TRUSTED_ALT_NAMES` | unset | Extra comma-separated SANs (`DNS:…`, `IP:…`) |

When internal SSL is on:

1. JupyterHub issues per-spawn Certipy certificates (localhost SANs).
2. The spawner copies key/cert/CA into the upload spool and lists them in
   `#SWM input-files` next to the Hub API token.
3. The job script sets `JUPYTERHUB_SSL_*` and uses `https://` for the service URL
   and hub API URL.
4. After the VM IP is known, the spawner opens a localhost TCP forward and the
   hub connects to `127.0.0.1` so hostname verification matches the cert SANs
   (TLS still terminates on the node).

Non-loopback hosts cannot disable internal SSL.

## Insecure lab mode

Use only on a trusted machine:

```bash
export SWM_JUPYTER_INSECURE_AUTH=1
export SWM_JUPYTER_BIND_IP=127.0.0.1
# optional: export SWM_JUPYTER_AUTH=dummy
```

The hub refuses insecure Dummy auth when the bind is not loopback.

## Per-user mTLS toward swm-core

Each JupyterHub login name must match a **local system user**. The spawner loads
that user's client certificate from the standard Sky Port paths:

| File | Path |
|------|------|
| Client cert | `$HOME/.swm/cert.pem` |
| Client key | `$HOME/.swm/key.pem` |
| CA chain | `$HOME/.swm/spool/secure/cluster/ca-chain-cert.pem` |

Optional CA override for all users: set `SWM_JUPYTER_CA_FILE` or
`c.SwmSpawner._swm_ca_file` to a readable CA chain path.

If the system user is missing, or the cert/key/CA file is missing or not
readable by the hub process, form render and job submit **fail**. There is no
fallback to a shared operator certificate.

### Provision one hub user

1. Create a system account whose name equals the JupyterHub login.
2. Create the SWM user with a fixed UUID: `swmctl user create <name> <uuid>`.
3. Issue a matching user cert: `swm-create-cert user <name> <uuid>`
   (do not use `swmctl user cert create`; it is unimplemented).
4. Install into that account's home:

```bash
install -d -m 0700 ~<name>/.swm/spool/secure/cluster
install -m 0644 $SWM_SPOOL/secure/users/<name>/cert.pem ~<name>/.swm/cert.pem
install -m 0600 $SWM_SPOOL/secure/users/<name>/key.pem ~<name>/.swm/key.pem
install -m 0644 $SWM_SPOOL/secure/cluster/ca-chain-cert.pem \
  ~<name>/.swm/spool/secure/cluster/ca-chain-cert.pem
```

5. Add the SWM user to the job account (`users` or `admins`).
6. Ensure the hub process can read the key (same uid, shared group with mode
   `0640`, or ACL). Private keys must not be world-readable.
7. Create the matching JupyterHub user (NativeAuthenticator / OAuth name).

swm-core maps identity from the cert UUID to the SWM user row (not from the
CN). The UUID in the cert must match the SWM user id. Do not give end users
the admin ACL certificate.

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

## Container user and certificates

The image runs as user `jupyterhub` (non-root).

For a single-user container demo, log in to the hub as `jupyterhub` and mount
that account's Sky Port files **read-only**:

| Host path | Container path |
|-----------|----------------|
| `~/.swm/cert.pem` | `/home/jupyterhub/.swm/cert.pem` |
| `~/.swm/key.pem` | `/home/jupyterhub/.swm/key.pem` |
| `~/.swm/spool/secure/cluster/ca-chain-cert.pem` | `/home/jupyterhub/.swm/spool/secure/cluster/ca-chain-cert.pem` |
| `~/.swm/jupyter-spawner.conf` (if present) | `/home/jupyterhub/.swm/jupyter-spawner.conf` |

Multi-user containers need a system account per hub login and a mount (or
copy) of each user's `~/.swm` into that account's home. Do not mount the whole
operator `~/.swm` tree as writable data for the hub.

## Related

- Sky Port trust model: swm-core `HOWTO/SECURITY.md`
