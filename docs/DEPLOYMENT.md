# Private remote access for one user

The supported default is a trusted, single-user workstation with HTTP bound to
`127.0.0.1`. This guide adds an HTTPS gateway for access to **your own** remote
instance. It does not turn SentinelML into a shared/lab service: every authenticated
request has full read/write access to all data. There is no tenant isolation,
project authorization, or application mutation audit trail.

## Host and secrets

Use a dedicated Linux host you administer. Keep the Compose HTTP binding on
`127.0.0.1:8888`; do not publish PostgreSQL or Redis. Restrict host/network access:
local processes and Docker administrators can bypass the gateway. Allow inbound
443 only from your VPN or trusted client addresses; restrict SSH similarly.

Install a maintained Nginx package and `apache2-utils` (for `htpasswd`) through your
OS package manager. Point a DNS name such as `sentinel.example.com` at the host and
provision a trusted TLS certificate with your CA/ACME tooling. Arrange certificate
renewal and Nginx reloads. This guide assumes the certificate/key paths below exist;
never use `curl -k` or disable certificate checks for real data.

Before the **first** Compose startup, copy `.env.docker.example` to
`.env.local.docker`, set its permissions to `0600`, and replace the default database
password. Keep `POSTGRES_PASSWORD` and the password in `DATABASE_URL` consistent;
URL-encode URI-special characters in the latter. These files remain ignored.
Changing environment files does not rotate a password in an existing database.

```sh
cp .env.docker.example .env.local.docker
chmod 600 .env.local.docker
# Edit credentials before starting the stack.
docker compose up -d --build --wait
sudo htpasswd -cB /etc/nginx/sentinelml.htpasswd owner
sudo chown root:www-data /etc/nginx/sentinelml.htpasswd
sudo chmod 640 /etc/nginx/sentinelml.htpasswd
```

`htpasswd` prompts privately; do not put passwords on command lines. Adjust
`www-data` to your distribution’s Nginx worker group. `-c` creates a new password
file: omit it when rotating an existing account. Do not reuse database credentials.

## Nginx configuration

Save [nginx.conf.example](nginx.conf.example) as
`/etc/nginx/conf.d/sentinelml.conf`, which must be included within Nginx’s `http`
context. Replace **every** `sentinel.example.com` and both certificate paths.
Disable the distribution’s default site if it conflicts. Keep only this gateway
on the chosen address/port; the configuration deliberately rejects unknown hosts.

```sh
sudo nginx -t
sudo systemctl reload nginx
```

All paths inherit HTTP Basic authentication, including `/ui/`, `/docs`,
`/openapi.json`, health routes, and API mutations. Credentials travel only over TLS.
The configuration rejects unexpected browser origins, limits request rates and
body size, and strips credentials before forwarding. Its access log records user,
method, path, status, and IP without query strings or request bodies. Limit log
permissions, retention, and backups: path identifiers remain potentially sensitive.
These are access logs, not a tamper-proof audit of changed data.

The first browser request prompts for your gateway credentials. For API checks,
`curl --user owner` prompts for a password. The included Python client has no
gateway-credential interface; use it locally (or over an SSH tunnel bound to your
local loopback), or use an HTTP client that supports Basic auth and verifies TLS.
Do not embed credentials in source code or URLs.

## Verify before entering real data

From the allowed client network, without credentials, verify **401** for each:

```sh
for path in /ui/ /docs /openapi.json /health/db /projects/; do
  curl --silent --output /dev/null --write-out '%{http_code}\n' \
    "https://sentinel.example.com$path"
done
```

Also verify an unauthenticated `POST /projects/` returns 401, invalid credentials
return 401, and `curl --user owner https://sentinel.example.com/health/db` returns
`{"status":"ok"}`. An authenticated POST with
`Origin: https://untrusted.example` must return **403** without creating a record.
On a disposable instance, confirm valid same-origin create/read requests work.
Burst requests above the configured limit should receive **429**; adjust the limit
to your workload without removing authentication. Check gateway logs for results.

From another machine, TCP connections to ports 8888, 5432, and 6379 must fail.
Confirm untrusted networks cannot reach 443 either. Check browser certificate
validation, password rotation, and the actual listening addresses after deploy.
Do not change the upstream bind to fix an access problem.

See official Nginx documentation for
[Basic authentication](https://nginx.org/en/docs/http/ngx_http_auth_basic_module.html),
[request limiting](https://nginx.org/en/docs/http/ngx_http_limit_req_module.html), and
[proxy headers](https://nginx.org/en/docs/http/ngx_http_proxy_module.html).
