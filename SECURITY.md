# Security

## Supported use

SentinelML 0.1 is a preview for one trusted user on a local workstation. The
application has **no authentication, authorization, or tenant isolation**. Anyone
who can reach its HTTP API can read and modify the experiment database.

The default Compose stack publishes HTTP only on `127.0.0.1`. PostgreSQL and Redis
have no published host ports. Its database credentials are local development
defaults. Changing a port binding or password does not add application access
control.

For access to your own remote instance, follow the
[HTTPS gateway guide](docs/DEPLOYMENT.md). It places authentication and request
limits in front of every route. It does not provide users, project permissions,
or a complete audit trail; shared hosting remains unsupported.

## Report a vulnerability

If **Security → Report a vulnerability** is available on this GitHub repository,
use it to send a private report. Include the affected version, impact, and steps
to reproduce with synthetic data.

If the private form is unavailable, ask a maintainer for a private reporting
channel **without posting the vulnerability details**. There is currently no
published fallback mailbox. Do not include credentials, experiment records, or
exploitable details in public issues.

Security fixes are handled on a best-effort basis for the current preview. There
is no guaranteed response time or maintenance commitment for older previews.

## Protect experiment data

Do not store passwords, API keys, access tokens, or private credentials in run
parameters, notes, catalog metadata, or source URLs. Exports, screenshots, logs,
and PostgreSQL backups may contain research data; share and retain them accordingly.

Back up PostgreSQL before changing versions and test restoring the dump in an
isolated instance. `docker compose down` preserves named volumes;
`docker compose down --volumes` and `make clean CONFIRM=YES` erase their contents.
See [Setup](docs/SETUP.md#back-up-your-history) and
[Release policy](docs/RELEASES.md#schema-and-upgrades).
