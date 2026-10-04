# Roadmap

[README](../README.md) / Roadmap

SentinelML currently focuses on local experiment history and scalar result
comparison. The items below are proposed directions, not shipped features or
release dates. Priorities can change as people use the project.

## Make the current workflow easier to grow

- **Schema migrations:** upgrade existing databases without starting over, with
  backup/restore and upgrade tests.
- **Bounded history queries:** server-side filtering, pagination, and export for
  workspaces that outgrow the current unpaginated lists.
- **More complete experiment context:** explicit code revision, command,
  environment, and dataset lineage, with careful handling of secrets.

## Extend experiment tracking

- **Metric history:** step-based values and learning curves alongside scalar
  summaries.
- **Artifacts:** references, checksums, and a storage interface for experiment
  files.
- **Integrations:** framework helpers and run groups where they simplify a
  concrete research workflow.

## Before shared workspaces

Shared deployment requires authentication, project permissions, workspace
isolation, API tokens, and audit history. The current local preview should not
be treated as a multi-user service.

Training orchestration, GPU scheduling, sweeps, and model serving are outside the
current scope. To propose work, open a feature request describing the workflow
and expected behavior; see [Contributing](../CONTRIBUTING.md).
