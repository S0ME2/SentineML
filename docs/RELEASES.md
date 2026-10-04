# Release and compatibility policy

[README](../README.md) / Release policy

## Preview scope

Version 0.1 is a local, single-user preview for fresh installations. Use the Python
client and server from the same version. HTTP routes are currently unversioned;
there is no cross-version client or schema compatibility guarantee.

Versions use `MAJOR.MINOR.PATCH`. Before 1.0, minor versions may introduce breaking
API, client, or schema changes. Patch versions should preserve those interfaces.
Breaking changes belong in the [changelog](../CHANGELOG.md).

## Tested baseline

| Component | Baseline |
| --- | --- |
| Python | 3.12 |
| PostgreSQL | 16 |
| Redis in Compose | 8.0 |
| Docker Compose | 2.24 or newer |
| Browser checks | Chromium via Playwright 1.63.0 |
| CI host | Linux x86-64, Ubuntu 24.04 |

Python package metadata allows newer Python versions, but the test baseline is
3.12. Other architectures and macOS/Windows Docker Desktop installations may work;
they are not tested platform commitments. The Makefile assumes a Unix-like shell.
Redis is optional in native application setup, but required by the supplied
Compose stack's startup dependencies.

## Schema and upgrades

There are no supported in-place schema upgrades in this preview.
[sql/database.sql](../sql/database.sql) creates a fresh schema transactionally and
refuses existing objects. Compose runs it only when initializing an empty database
volume. Updating that file does not update an existing database.

Before trying a release with a different schema:

1. Back up the working instance with `make backup`. Keep the dump private and
   record the source version.
2. Test recovery into a separate, empty PostgreSQL 16 instance using the **same**
   SentinelML version. `pg_restore --exit-on-error --no-owner` can restore the
   custom-format dump; use your isolated target connection.
3. Start the new release in a separate Compose project with empty volumes and a
   different HTTP port. For example, from the new checkout:

   ```sh
   APP_PORT=8889 docker compose -p sentinelml-preview-new up -d --build --wait
   ```

   Check override files and environment variables first. A project name isolates
   the default volumes; an overridden `DATABASE_URL` can still point elsewhere.
4. Keep the old instance and volumes until you have decided what to retain. Do not
   attach old data volumes to an incompatible schema. Moving history between
   schemas needs a reviewed migration.

A browser export is not a full backup. A restore test confirms recovery of the
source schema, not compatibility with a newer one. If preserving history across
versions is essential, stay on the original version until a migration is available.

## Dependencies and distributions

`pyproject.toml` is the authored Python dependency manifest; `uv.lock` records its
resolution. Use `uv sync --locked` for the tested dependency set. The build backend,
container images, Dockerfile frontend, and GitHub Actions are pinned to versions,
digests, or commit SHAs. Runner images, OS packages, and downloaded browser
libraries can still change.

When changing dependencies, update the manifest and lockfile together, review
upstream changes, and rerun lint, unit, HTTP, browser, and fresh-build checks.
Playwright is installed dynamically for tests; its transitive dependencies and
Chromium/system libraries are not governed by `uv.lock`.

### Build locally

```sh
uv build
uv run python tests/check_distribution.py dist
```

These commands build and inspect files; they do not publish a package.

| Artifact | Contents |
| --- | --- |
| Wheel | Server, Python client, dashboard, bundled fonts/icons, and licenses |
| Source archive | Python code plus Compose, initialization SQL, docs, tests, examples, and lockfile |

The wheel does not provision PostgreSQL or include the initialization SQL. Configure
`DATABASE_URL` and initialize a database using the source archive before starting
an installed server:

```sh
python -m uvicorn app.main:app --host 127.0.0.1 --port 8888
```

A plain pip install resolves transitive dependencies at installation time. Use the
source checkout with `uv sync --locked` when you need the tested resolution; CI
checks wheel installation with constraints exported from `uv.lock`.

Docker Compose is the recommended first-run path. There is currently no published
PyPI installation workflow.
