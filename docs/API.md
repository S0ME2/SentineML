# HTTP API reference

[README](../README.md) / [Usage](USAGE.md) / HTTP API

Default base URL: `http://127.0.0.1:8888`. Requests and responses use JSON, except
successful deletes, which return `204` with no body. Lists are unpaginated.

For request fields, response schemas, and interactive calls, open
[Swagger UI](http://127.0.0.1:8888/docs) on your running instance. The machine-readable
schema is at `/openapi.json`. See [run states](USAGE.md#run-states) before writing
parameters or metrics.

## Make a request

With the server running, create a project:

```sh
curl --fail-with-body --silent --show-error \
  http://127.0.0.1:8888/projects/ \
  -H 'Content-Type: application/json' \
  -d '{"name":"http-example","description":"First API request"}'
```

The response has this shape; the ID is assigned by the server:

```json
{"id": 1, "name": "http-example", "description": "First API request"}
```

Use the returned ID in later requests. Reusing a project name returns `409`;
choose another name or retrieve the existing project. For a complete tracking
workflow that handles returned IDs, use the [Python example](../examples/track_experiment.py).

`--fail-with-body` requires curl 7.76 or newer. With older curl, use `--fail` to
check failures, or omit that flag to inspect the response body yourself.

## Root and health

| Method | Endpoint | What it does | Notes |
| --- | --- | --- | --- |
| `GET` | `/` | Returns a welcome message | Quick API reachability check |
| `GET` | `/health/` | Returns API health | Returns `{"status":"ok"}` while the app is serving requests |
| `GET` | `/health/db` | Checks PostgreSQL connectivity | Returns `status: ok` or `status: error` |
| `GET` | `/health/redis` | Checks Redis connectivity | Returns `error` when Redis is unavailable or not configured |

## Projects

| Method | Endpoint | What it does | Important behavior |
| --- | --- | --- | --- |
| `GET` | `/projects/` | List projects | Reads the collection from PostgreSQL |
| `GET` | `/projects/{project_id}` | Get one project | Uses project cache-aside behavior when Redis is configured |
| `POST` | `/projects/` | Create a project | Project names are unique |
| `PATCH` | `/projects/{project_id}` | Update name and/or description | Cache entry is invalidated after commit |
| `DELETE` | `/projects/{project_id}` | Delete a project | Conflicts when existing runs reference it |
| `GET` | `/projects/{project_id}/best-run?metric_name=...` | Return the best completed, non-ignored run | Uses the metric direction; requires a matching run |
| `GET` | `/projects/{project_id}/runs/compare?metric_name=...` | Return ranked completed runs | Ignored runs are excluded; requires a matching run |

## Datasets

| Method | Endpoint | What it does | Important behavior |
| --- | --- | --- | --- |
| `GET` | `/datasets/` | List datasets | — |
| `GET` | `/datasets/{dataset_id}` | Get one dataset | — |
| `POST` | `/datasets/` | Register a dataset version | `(name, version)` is unique |
| `PATCH` | `/datasets/{dataset_id}` | Update dataset metadata | Supports name, version, description, hash, source, metadata |
| `DELETE` | `/datasets/{dataset_id}` | Delete a dataset | Conflicts when a run references it |

## Models

| Method | Endpoint | What it does | Important behavior |
| --- | --- | --- | --- |
| `GET` | `/models/` | List models | — |
| `GET` | `/models/{model_id}` | Get one model | — |
| `POST` | `/models/` | Register a model version | `(name, version)` is unique |
| `PATCH` | `/models/{model_id}` | Update model metadata | Supports name, version, description, type, metadata |
| `DELETE` | `/models/{model_id}` | Delete a model | Conflicts when a run references it |

## Runs

| Method | Endpoint | What it does | Important behavior |
| --- | --- | --- | --- |
| `GET` | `/runs/` | List all runs | — |
| `GET` | `/runs/{run_id}` | Get one run | — |
| `POST` | `/runs/` | Create a run | Project, dataset, and model must exist; starts as `waiting` |
| `PATCH` | `/runs/{run_id}` | Update run fields | Dataset/model only in `waiting`; reason only for failed/cancelled runs |
| `DELETE` | `/runs/{run_id}` | Delete a run | Only `waiting` runs can be deleted |
| `POST` | `/runs/{run_id}/start` | Move `waiting` → `running` | Requires at least one parameter |
| `POST` | `/runs/{run_id}/complete` | Move `running` → `completed` | Requires at least one metric |
| `POST` | `/runs/{run_id}/fail?reason=...` | Move `running` → `failed` | Failure reason is required |
| `POST` | `/runs/{run_id}/cancel?reason=...` | Cancel a waiting or running run | Reason is optional |
| `POST` | `/runs/{run_id}/ignore?ignore_reason=...` | Exclude a run from ranking | Reason is required; record remains stored |
| `POST` | `/runs/{run_id}/unignore` | Re-enable a previously ignored run | Ranking still requires `completed` state |

## Parameters

| Method | Endpoint | What it does | Important behavior |
| --- | --- | --- | --- |
| `GET` | `/runs/{run_id}/parameters/` | List parameters for a run | Run must exist |
| `GET` | `/runs/{run_id}/parameters/{parameter_id}` | Get one parameter | Scoped to the run |
| `POST` | `/runs/{run_id}/parameters/` | Add a parameter | Run must be `waiting`; name is unique within the run |
| `PATCH` | `/runs/{run_id}/parameters/{parameter_id}` | Update a parameter | Run must be `waiting` |
| `DELETE` | `/runs/{run_id}/parameters/{parameter_id}` | Delete a parameter | Run must be `waiting` |

## Metrics

| Method | Endpoint | What it does | Important behavior |
| --- | --- | --- | --- |
| `GET` | `/runs/{run_id}/metrics/` | List metrics for a run | Run must exist |
| `GET` | `/runs/{run_id}/metrics/{metric_id}` | Get one metric | Scoped to the run |
| `POST` | `/runs/{run_id}/metrics/` | Add a metric | Run must be `running`; matching metric direction must exist |
| `PATCH` | `/runs/{run_id}/metrics/{metric_id}` | Update a metric | Run must be `running`; renamed metric also needs a direction |
| `DELETE` | `/runs/{run_id}/metrics/{metric_id}` | Delete a metric | Run must be `running` |

## Metric directions

| Method | Endpoint | What it does | Important behavior |
| --- | --- | --- | --- |
| `GET` | `/metric-directions/` | List metric directions | — |
| `GET` | `/metric-directions/{metric_name}` | Get one metric direction | Metric name is the identifier |
| `POST` | `/metric-directions/` | Define maximize/minimize semantics | Must exist before a metric with that name is logged |
| `PATCH` | `/metric-directions/{metric_name}` | Change `maximize` | Rejected once metrics already use that direction |
| `DELETE` | `/metric-directions/{metric_name}` | Delete a metric direction | Conflicts when metrics reference it |

## Validation and errors

| Status | Meaning | Typical cause |
| --- | --- | --- |
| `400` | Request conflicts with an application rule | Starting without parameters, writing metrics after completion, or requesting a ranking with no eligible runs |
| `404` | Resource not found | Unknown ID or undefined metric direction |
| `409` | Uniqueness or reference conflict | Duplicate project/name-version pair, or deleting a catalog record used by a run |
| `422` | Request fails schema validation | Missing fields, overlong text, or a non-finite metric value |

Application errors have a string `detail`, for example:

```json
{"detail": "Project with id 123 not found"}
```

Validation errors have a list of details identifying the invalid fields. Raw
request values and validator context are omitted from those details.

### Field limits

| Fields | Maximum characters |
| --- | --- |
| Project, dataset, model, parameter, metric, and metric-direction names | 255 |
| Dataset/model versions, dataset hashes, model types, parameter values | 255 |
| Parameter `value_type` | 100 |

Limits apply to create and update requests. Names and required parameter values
are trimmed by the domain; empty required text is rejected. Notes, descriptions,
source, and metadata use database text fields without these length limits.
Metric values must be finite numbers.

### Updates

`PATCH` changes supplied fields. Omitted fields remain unchanged. Nullable fields
such as notes can be cleared with `null`; required fields such as names cannot.
An empty update is rejected. See Swagger for the fields accepted by each resource.

### Health checks

`/health/` checks that the API is responding. `/health/db` and `/health/redis`
return a JSON `status` of `ok` or `error`; an HTTP `200` alone does not establish
that those dependencies are healthy. Redis reports `error` when it is disabled.

The supplied Compose stack waits for a successful database health check before
considering the app healthy.
