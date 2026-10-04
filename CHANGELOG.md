# Changelog

User-visible changes to SentinelML. Version 0.1.0 is an unreleased preview.

## 0.1.0 — Unreleased

### Experiment tracking

- Organize runs into projects with dataset and model version records.
- Record parameters, notes, and finite scalar metrics through the HTTP API or
  dependency-free Python client.
- Start, complete, fail, and cancel runs with lifecycle validation. Lock
  parameters after start and metrics after completion.
- Ignore a run with a reason while keeping its history. Rank completed,
  non-ignored runs using explicit minimize/maximize directions.

### Dashboard

- Browse and filter experiments by project, status, text, and activity.
- Compare selected runs, parameters, and scalar metrics side by side.
- Export the filtered run list and basic metadata as CSV or JSON.
- Create catalog records and record run lifecycle actions from the browser.
- Guide first-run metric registration and register new metrics from run details.
- Edit waiting-run parameters and running-run metrics from the dashboard.
- Preserve unsaved run notes across navigation and lifecycle changes, and warn
  before reloading or closing the page with drafts.

### Local installation

- Start the application, PostgreSQL, and Redis with Docker Compose.
- Create non-overwriting PostgreSQL backups with `make backup`.
- Build a wheel containing the server, Python client, dashboard, and asset licenses.

### Validation fixes

- Reject overlong fields with validation errors instead of database failures.
- Reject non-finite metric values.
- Update the existing scalar metric when repeated Python logging uses names with
  surrounding whitespace.

This preview supports one trusted user and fresh installations. Authentication,
metric time series, artifact storage, and schema migrations are not included.
See [current limits](README.md#current-limits) and [Release policy](docs/RELEASES.md).
