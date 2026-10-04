# Contributing

[README](README.md) / Contributing

Bug reports, documentation corrections, and improvements to experiment tracking
are welcome. For a larger feature, open an issue first so the workflow and scope
can be discussed before implementation.

## Report a problem

Use the **Bug report** issue form. Include:

- What you did, what happened, and what you expected.
- A minimal reproduction using synthetic data.
- Installation method, operating system, Python/Compose version, and browser.
- The relevant error output, with credentials and private data removed.

For a feature request, describe the experiment workflow you cannot complete and
an example of the result you need. Report security issues through
[SECURITY.md](SECURITY.md), rather than posting vulnerability details publicly.

## Set up development

Use **Python 3.12**, **uv 0.11.28**, and Docker Compose **2.24 or newer**. From the
repository root:

```sh
uv sync --locked
make lint
make test
```

Unit tests need no running database. The dashboard uses plain HTML, CSS, and
JavaScript; no npm install or frontend build is required.

For a local instance to explore, follow [Setup](docs/SETUP.md). For editing the
Python API with reload enabled, follow its [native setup](docs/SETUP.md#native-python).
[Architecture](docs/ARCHITECTURE.md) maps the code paths.

## Test against PostgreSQL

HTTP and browser tests create persistent synthetic records. Use a disposable
Compose project with its own volumes and an unused port:

```sh
APP_PORT=18888 docker compose -p sentinelml-dev-test up -d --build --wait
SENTINELML_TEST_URL=http://127.0.0.1:18888 \
  uv run python -m unittest discover -s tests/integration -v
```

Before starting, check `.env.local.docker` and exported configuration variables.
A separate project isolates the default volumes, but an overridden `DATABASE_URL`
can still point at an existing database. Use the checked-in development defaults
or credentials for a database dedicated to tests.

### Browser workflows

Install the optional Chromium test runtime, then run the three suites against
the same disposable instance:

```sh
uv run --with playwright==1.63.0 python -m playwright install chromium
uv run --with playwright==1.63.0 python tests/browser/smoke.py --url http://127.0.0.1:18888
uv run --with playwright==1.63.0 python tests/browser/insights.py --url http://127.0.0.1:18888
uv run --with playwright==1.63.0 python tests/browser/catalog.py --url http://127.0.0.1:18888
```

On Linux, missing browser libraries can be installed with Playwright's
`install --with-deps chromium` command. These are test dependencies; they do not
ship with the dashboard. CI runs all three suites.

Stop the test stack when finished:

```sh
docker compose -p sentinelml-dev-test down
```

This preserves test volumes. Add `--volumes` only when you intend to delete that
project's test data. Do not use the test suite against your working history.

## Check distributions

```sh
uv build
uv run python tests/check_distribution.py dist
```

The check inspects the source archive and wheel for server/client code, dashboard
assets, licenses, and unwanted local state. Build/dependency behavior is described
in [Release policy](docs/RELEASES.md#dependencies-and-distributions).

## Submit a change

Keep the pull request focused on one problem. Explain the behavior before and
after your change, include the checks you ran, and add screenshots for UI changes.
Include a regression test for behavior that could break again.

- Put entity and lifecycle rules in `app/domain`, workflow coordination in
  `app/application`, and HTTP/database adapters at the edges.
- Preserve existing routes and lifecycle invariants. Document compatibility
  changes explicitly.
- Keep the dashboard usable by keyboard and at 320px and desktop widths. Check
  empty, loading, populated, and failure states when changing an interaction.
- Use safe DOM APIs for server-provided text. Discuss external fonts, analytics,
  and new runtime network dependencies before adding them.
- Discuss schema changes first: initialization SQL is not a migration, and this
  preview has no supported upgrade path.
- Update the affected guide and [changelog](CHANGELOG.md) when behavior changes.

Run `make lint`, `make test`, and checks relevant to your change before submitting.
`make format` applies Python formatting. Keep `pyproject.toml` and `uv.lock` in
sync; do not add a second authored dependency manifest.

Follow the [Code of Conduct](CODE_OF_CONDUCT.md) in issues and pull requests.
