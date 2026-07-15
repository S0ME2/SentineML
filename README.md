<div align="center">

<img src="assets/sentinelml-logo.png" alt="SentinelML logo" width="180">

# SentinelML

### Structured experiment history. Explicit lifecycle rules. Honest comparisons.

**A FastAPI backend for recording machine-learning experiment metadata, preserving run history, and comparing completed runs without letting invalid experiments quietly rewrite the story.**

[![Python](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.139-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-4169E1?logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![Redis](https://img.shields.io/badge/Redis-8-DC382D?logo=redis&logoColor=white)](https://redis.io/)

[Understand it](#the-problem-in-one-minute) · [Run it](#run-it) · [Use the API](#using-sentinelml) · [See the engineering](#what-happens-when-things-go-wrong) · [Check a feature](#can-sentinelml-do-x) · [Develop it](#developing-sentinelml)

</div>

![SentinelML — turning scattered experiment metadata into trustworthy history](assets/sentinelml-hero.png)

---

<table>
<tr>
<td width="33%" valign="top">
<h3>Track</h3>
Projects, dataset versions, model versions, runs, parameters, metrics, notes, and metric direction.
</td>
<td width="33%" valign="top">
<h3>Protect</h3>
Lifecycle rules, transaction boundaries, PostgreSQL integrity, and row locks constrain how experiment history may change.
</td>
<td width="33%" valign="top">
<h3>Compare</h3>
Rank completed runs by metrics that can be maximized or minimized, while preserving ignored runs outside the ranking.
</td>
</tr>
</table>

> [!NOTE]
> **SentinelML is intentionally focused.** It records and compares experiment metadata. It does **not** train models, schedule GPUs, store artifacts, or try to replace a full platform such as MLflow or Weights & Biases.

## Choose your path

| You came here to... | Start here |
| --- | --- |
| **Understand the idea without backend jargon** | [The problem in one minute](#the-problem-in-one-minute) |
| **Get it running locally** | [Run it](#run-it) |
| **Use the project through HTTP / Swagger** | [Using SentinelML](#using-sentinelml) |
| **Decide whether it has a feature you need** | [Can SentinelML do X?](#can-sentinelml-do-x) |
| **Review the backend engineering** | [What happens when things go wrong?](#what-happens-when-things-go-wrong) |
| **Understand the codebase** | [Architecture](#architecture) |
| **Change or extend the project** | [Developing SentinelML](#developing-sentinelml) |

---

## The problem in one minute

> **“This run reached 94% accuracy.”**
>
> Great. Now answer the questions that make that number useful.

- Which dataset **version** produced it?
- Which model version and parameters were used?
- Was the result valid, or should it be excluded from comparison?
- Is the metric supposed to go **up** or **down**?
- Can the run be silently edited after the experiment is over?
- If two requests modify the same run at the same time, which state wins?

SentinelML treats an experiment record less like a loose spreadsheet row and more like a **lab notebook with rules**.

```mermaid
flowchart LR
    Work["Training code / notebook / external job"]
    API["SentinelML API<br/>experiment metadata"]
    PG[("PostgreSQL<br/>durable source of truth")]
    Redis[("Redis<br/>optional project cache")]
    Result["Queryable history<br/>+ best-run comparison"]

    Work -->|HTTP calls| API
    API --> PG
    API -. cache-aside .-> Redis
    PG --> Result
```

**The training happens somewhere else.** SentinelML records the context and outcome around that training run.

### A 60-second experiment story

```mermaid
flowchart LR
    A["1 · Register context<br/>Project · Dataset · Model"]
    B["2 · Prepare<br/>waiting<br/>Add parameters"]
    C["3 · Execute<br/>running<br/>Record metrics"]
    D["4 · Preserve<br/>completed · failed · cancelled"]
    E["5 · Compare<br/>Rank valid completed runs"]
    I["Ignored run<br/>Preserved, not ranked"]

    A --> B --> C --> D --> E
    D -. keep history .-> I
```

The important idea is simple: **context comes first, parameters belong to setup, metrics belong to execution, and completed history is preserved before comparison happens.**

### Tiny example: preserve the bad run, protect the ranking

Assume `accuracy` is configured as **maximize**:

| Run | Accuracy | State | Ranking |
| --- | ---: | --- | --- |
| `#17` | `0.91` | completed | Included |
| `#18` | **`0.94`** | completed | **Best valid run** |
| `#19` | `0.97` | completed + ignored | Excluded |

Run `#19` stays in history with an ignore reason. The record is not erased, but it no longer contaminates the answer to “which run should I trust for comparison?”

---

## Run it

The shortest path is Docker Compose. The stack starts:

```text
FastAPI API  +  PostgreSQL  +  Redis
```

### 1. Create `.env.local.docker`

The Compose file expects this file in the repository root. Use development-only values and keep real credentials out of version control.

```dotenv
POSTGRES_USER=sentinelml
POSTGRES_PASSWORD=change-me
POSTGRES_DB=sentinelml

DATABASE_URL=postgresql://sentinelml:change-me@db:5432/sentinelml
REDIS_URL=redis://redis:6379/0
PROJECT_CACHE_TTL_SECONDS=300
```

### 2. Build and start

```bash
make build
```

Equivalent command:

```bash
docker compose up -d --build
```

### 3. Confirm the stack is healthy

```bash
make ps
curl http://127.0.0.1:8888/health/
```

Expected API response:

```json
{"status":"ok"}
```

Then open Swagger UI:

```text
http://127.0.0.1:8888/docs
```

| Check | URL |
| --- | --- |
| Swagger UI | `http://127.0.0.1:8888/docs` |
| OpenAPI schema | `http://127.0.0.1:8888/openapi.json` |
| API health | `http://127.0.0.1:8888/health/` |
| PostgreSQL health | `http://127.0.0.1:8888/health/db` |
| Redis health | `http://127.0.0.1:8888/health/redis` |

<details>
<summary><strong>Run the Python API locally with uv</strong></summary>

<br>

Install dependencies:

```bash
uv sync
```

Provide local environment variables through `.env.local` or your shell. Example for services available on localhost:

```dotenv
DATABASE_URL=postgresql://sentinelml:change-me@localhost:5432/sentinelml
REDIS_URL=redis://localhost:6379/0
PROJECT_CACHE_TTL_SECONDS=300
```

Start the API:

```bash
make start
```

Equivalent command:

```bash
uv run uvicorn app.main:app --reload --host 127.0.0.1 --port 8888
```

`REDIS_URL` is optional at the application level. Without it, SentinelML uses a no-op project cache.

</details>

<details>
<summary><strong>Troubleshooting the first run</strong></summary>

<br>

### Compose says the environment file is missing

Create `.env.local.docker` in the repository root. The supplied `docker-compose.yaml` references it directly.

### PostgreSQL schema changes are not appearing

`sql/database.sql` is mounted into PostgreSQL's initialization directory. PostgreSQL initialization scripts run when the database volume is created for the first time.

For disposable local data, recreate the volumes:

```bash
make clean
make build
```

> `make clean` deletes the local Compose volumes and therefore deletes local PostgreSQL and Redis data.

### The API container does not start because Redis is unhealthy

The **application code** can operate without Redis, but the provided Compose stack declares Redis as a healthy startup dependency. For the Compose configuration as written, Redis must become healthy before the API container starts.

### Something is already using port `8888`

Stop the other process or change the host port mapping in `docker-compose.yaml`.

### I need container logs

```bash
docker compose logs -f app
docker compose logs -f db
docker compose logs -f redis
```

</details>

---

## Using SentinelML

SentinelML does **not** have a custom web UI yet. Today, the product interface is its HTTP API, and the easiest way to explore it manually is FastAPI's interactive Swagger UI:

```text
http://127.0.0.1:8888/docs
```

Your training script, notebook, CI job, or another service can call the same endpoints directly.

```mermaid
flowchart LR
    User["You / notebook / training job"]
    Swagger["Swagger UI"]
    API["SentinelML HTTP API"]
    PG[("PostgreSQL")]
    Redis[("Redis cache")]
    History["Experiment history<br/>+ ranked results"]

    User -->|HTTP| API
    Swagger -->|interactive HTTP| API
    API --> PG
    API -. project cache .-> Redis
    PG --> History
```

### Typical experiment workflow

```mermaid
flowchart LR
    A["Create project"] --> B["Register dataset"]
    B --> C["Register model"]
    C --> D["Define metric direction"]
    D --> E["Create waiting run"]
    E --> F["Add parameters"]
    F --> G["Start run"]
    G --> H["Log metrics"]
    H --> I["Complete run"]
    I --> J["Compare runs"]
    J --> K["Best run"]
```

The API is deliberately lifecycle-aware. The order above is not just documentation—the application enforces it.

### What can change at each run state?

| Run state | Parameters | Metrics | Dataset / model | Delete run | Lifecycle actions | Ranking |
| --- | --- | --- | --- | --- | --- | --- |
| `waiting` | Create / update / delete | No | Can change | Yes | Start or cancel | No |
| `running` | No | Create / update / delete | Locked | No | Complete, fail, or cancel | No |
| `completed` | Locked | Locked | Locked | No | — | Yes, when non-ignored and the metric exists |
| `failed` | Locked | Locked | Locked | No | — | No |
| `cancelled` | Locked | Locked | Locked | No | — | No |

A run's `notes` can be updated independently of the lifecycle. A `reason` can be updated for failed or cancelled runs. Ignore/unignore is separate from lifecycle state; only **completed, non-ignored** runs participate in comparison.

### API at a glance

| Area | What it is for |
| --- | --- |
| **Projects** | Organize experiments and query ranked/best runs |
| **Datasets** | Register dataset names, versions, hashes, sources, and metadata |
| **Models** | Register model names, versions, types, and metadata |
| **Runs** | Connect project + dataset + model and control the experiment lifecycle |
| **Parameters** | Record configuration while a run is `waiting` |
| **Metrics** | Record numeric outcomes while a run is `running` |
| **Metric directions** | Define whether a metric should be maximized or minimized |
| **Health** | Check the API, PostgreSQL, and Redis adapters |

> [!TIP]
> Start with Swagger UI when exploring manually. Use the endpoint reference below when integrating SentinelML into scripts or services.

<details>
<summary><strong>Use SentinelML end to end in a few requests</strong></summary>

<br>

This walkthrough assumes each newly created resource receives ID `1`.

#### 1. Create a project

```bash
curl -X POST "http://127.0.0.1:8888/projects/" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "image-classification",
    "description": "Baseline image classification experiments"
  }'
```

#### 2. Register a dataset

```bash
curl -X POST "http://127.0.0.1:8888/datasets/" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "cifar-10",
    "version": "1.0",
    "source": "torchvision"
  }'
```

#### 3. Register a model

```bash
curl -X POST "http://127.0.0.1:8888/models/" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "resnet",
    "version": "18",
    "model_type": "cnn"
  }'
```

#### 4. Tell SentinelML how to rank `accuracy`

```bash
curl -X POST "http://127.0.0.1:8888/metric-directions/" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "accuracy",
    "maximize": true
  }'
```

Use `maximize: false` for metrics where lower is better, such as many loss or latency measurements.

#### 5. Create a run

```bash
curl -X POST "http://127.0.0.1:8888/runs/" \
  -H "Content-Type: application/json" \
  -d '{
    "project_id": 1,
    "dataset_id": 1,
    "model_id": 1,
    "notes": "Baseline run"
  }'
```

A new run starts in `waiting`.

#### 6. Add at least one parameter

```bash
curl -X POST "http://127.0.0.1:8888/runs/1/parameters/" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "learning_rate",
    "value": "0.001",
    "value_type": "float"
  }'
```

#### 7. Start the run

```bash
curl -X POST "http://127.0.0.1:8888/runs/1/start"
```

Starting is rejected if the run has no parameters.

#### 8. Record a metric while the run is running

```bash
curl -X POST "http://127.0.0.1:8888/runs/1/metrics/" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "accuracy",
    "value": 0.94,
    "notes": "Validation accuracy"
  }'
```

The corresponding metric direction must already exist.

#### 9. Complete the run

```bash
curl -X POST "http://127.0.0.1:8888/runs/1/complete"
```

Completion is rejected if the running run has no metrics.

#### 10. Ask for the best run

```bash
curl "http://127.0.0.1:8888/projects/1/best-run?metric_name=accuracy"
```

Or retrieve the full ranking:

```bash
curl "http://127.0.0.1:8888/projects/1/runs/compare?metric_name=accuracy"
```

</details>

<details>
<summary><strong>Show the complete endpoint reference</strong></summary>

<br>

#### Root and health

| Method | Endpoint | What it does | Notes |
| --- | --- | --- | --- |
| `GET` | `/` | Returns a welcome message | Quick API reachability check |
| `GET` | `/health/` | Returns API health | Returns `{"status":"ok"}` while the app is serving requests |
| `GET` | `/health/db` | Checks PostgreSQL connectivity | Returns `status: ok` or `status: error` |
| `GET` | `/health/redis` | Checks Redis connectivity | Returns `error` when Redis is unavailable or not configured |

#### Projects

| Method | Endpoint | What it does | Important behavior |
| --- | --- | --- | --- |
| `GET` | `/projects/` | List projects | Reads the collection from PostgreSQL |
| `GET` | `/projects/{project_id}` | Get one project | Uses project cache-aside behavior when Redis is configured |
| `POST` | `/projects/` | Create a project | Project names are unique |
| `PATCH` | `/projects/{project_id}` | Update name and/or description | Cache entry is invalidated after commit |
| `DELETE` | `/projects/{project_id}` | Delete a project | Conflicts when existing runs reference it |
| `GET` | `/projects/{project_id}/best-run?metric_name=...` | Return the highest-ranked valid run | Direction can be maximize or minimize |
| `GET` | `/projects/{project_id}/runs/compare?metric_name=...` | Return ranked completed runs | Ignored runs are excluded |

#### Datasets

| Method | Endpoint | What it does | Important behavior |
| --- | --- | --- | --- |
| `GET` | `/datasets/` | List datasets | — |
| `GET` | `/datasets/{dataset_id}` | Get one dataset | — |
| `POST` | `/datasets/` | Register a dataset version | `(name, version)` is unique |
| `PATCH` | `/datasets/{dataset_id}` | Update dataset metadata | Supports name, version, description, hash, source, metadata |
| `DELETE` | `/datasets/{dataset_id}` | Delete a dataset | Conflicts when a run references it |

#### Models

| Method | Endpoint | What it does | Important behavior |
| --- | --- | --- | --- |
| `GET` | `/models/` | List models | — |
| `GET` | `/models/{model_id}` | Get one model | — |
| `POST` | `/models/` | Register a model version | `(name, version)` is unique |
| `PATCH` | `/models/{model_id}` | Update model metadata | Supports name, version, description, type, metadata |
| `DELETE` | `/models/{model_id}` | Delete a model | Conflicts when a run references it |

#### Runs

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

#### Parameters

| Method | Endpoint | What it does | Important behavior |
| --- | --- | --- | --- |
| `GET` | `/runs/{run_id}/parameters/` | List parameters for a run | Run must exist |
| `GET` | `/runs/{run_id}/parameters/{parameter_id}` | Get one parameter | Scoped to the run |
| `POST` | `/runs/{run_id}/parameters/` | Add a parameter | Run must be `waiting`; name is unique within the run |
| `PATCH` | `/runs/{run_id}/parameters/{parameter_id}` | Update a parameter | Run must be `waiting` |
| `DELETE` | `/runs/{run_id}/parameters/{parameter_id}` | Delete a parameter | Run must be `waiting` |

#### Metrics

| Method | Endpoint | What it does | Important behavior |
| --- | --- | --- | --- |
| `GET` | `/runs/{run_id}/metrics/` | List metrics for a run | Run must exist |
| `GET` | `/runs/{run_id}/metrics/{metric_id}` | Get one metric | Scoped to the run |
| `POST` | `/runs/{run_id}/metrics/` | Add a metric | Run must be `running`; matching metric direction must exist |
| `PATCH` | `/runs/{run_id}/metrics/{metric_id}` | Update a metric | Run must be `running`; renamed metric also needs a direction |
| `DELETE` | `/runs/{run_id}/metrics/{metric_id}` | Delete a metric | Run must be `running` |

#### Metric directions

| Method | Endpoint | What it does | Important behavior |
| --- | --- | --- | --- |
| `GET` | `/metric-directions/` | List metric directions | — |
| `GET` | `/metric-directions/{metric_name}` | Get one metric direction | Metric name is the identifier |
| `POST` | `/metric-directions/` | Define maximize/minimize semantics | Must exist before a metric with that name is logged |
| `PATCH` | `/metric-directions/{metric_name}` | Change `maximize` | Rejected once metrics already use that direction |
| `DELETE` | `/metric-directions/{metric_name}` | Delete a metric direction | Conflicts when metrics reference it |

#### Error responses

Application-level errors are translated at the HTTP edge:

| Status | Meaning in SentinelML |
| --- | --- |
| `400 Bad Request` | Invalid data, invalid lifecycle action, or empty/unsupported update |
| `404 Not Found` | Requested project, dataset, model, run, parameter, metric, or direction does not exist |
| `409 Conflict` | Uniqueness/integrity conflict or a resource is still in use |

FastAPI/Pydantic request validation can also return its standard `422 Unprocessable Entity` response before an application use case runs.

</details>

---

## What happens when things go wrong?

This is where SentinelML becomes more interesting than a CRUD demo.

![SentinelML keeps PostgreSQL as the source of truth when the cache fails](assets/sentinelml-resilience.png)

| Situation | Behavior | Why it matters |
| --- | --- | --- |
| **Redis is unavailable during a project read** | Cache failure is treated as a miss; the read falls back to PostgreSQL. | The cache improves reads without becoming the durable source of truth. |
| **Redis is not configured** | A null-cache implementation is used. | Core application behavior does not require caching. |
| **Two mutation workflows target the same protected row** | Repository methods use PostgreSQL `SELECT ... FOR UPDATE` for relevant write paths. | Concurrent business operations do not blindly race on the same loaded state. |
| **A lifecycle rule is violated** | The domain/application rejects the action instead of relying on the client to “behave.” | Invalid transitions stay invalid across HTTP or future interfaces. |
| **A use case exits without a successful commit** | The Unit of Work rolls back the transaction and closes the session. | A business operation has an explicit transaction boundary. |
| **A completed run is discovered to be invalid** | It can be marked ignored with a reason while remaining stored. | History and comparison are separated instead of deleting inconvenient evidence. |
| **A referenced resource is missing or conflicts** | Application errors are translated to HTTP `404`, `400`, or `409` responses. | HTTP stays an edge concern rather than leaking into the domain. |

### The run lifecycle is a state machine, not a suggestion

```mermaid
stateDiagram-v2
    [*] --> waiting
    waiting --> running: start · requires parameter
    waiting --> cancelled: cancel
    running --> completed: complete · requires metric
    running --> failed: fail · requires reason
    running --> cancelled: cancel
    completed --> [*]
    failed --> [*]
    cancelled --> [*]
```

| Try this | Result |
| --- | --- |
| Start a run with no parameters | Rejected |
| Edit parameters after the run starts | Rejected |
| Add metrics before the run starts | Rejected |
| Complete a run with no metrics | Rejected |
| Delete a run after it has started | Rejected |
| Fail a run without a reason | Rejected |
| Include an ignored run in best-run ranking | Excluded |

---

## The engineering, with receipts

| Engineering problem | SentinelML's approach | Code |
| --- | --- | --- |
| **Business rules should survive outside FastAPI** | Lifecycle and validation behavior live in framework-independent domain objects. | [`app/domain/runs.py`](app/domain/runs.py) |
| **Application actions need explicit orchestration** | Use cases coordinate domain behavior through ports. | [`app/application/use_cases/`](app/application/use_cases/) |
| **Multi-repository work needs one transaction boundary** | An explicit Unit of Work owns commit/rollback behavior. | [`app/application/ports/unit_of_work.py`](app/application/ports/unit_of_work.py) · [`app/infrastructure/postgres/unit_of_work.py`](app/infrastructure/postgres/unit_of_work.py) |
| **Concurrent mutations can race** | PostgreSQL repository paths use row locking where mutation workflows require it. | [`app/infrastructure/postgres/repositories/`](app/infrastructure/postgres/repositories/) |
| **Persistence should not define the domain model** | SQLAlchemy ORM objects are mapped to and from domain entities. | [`app/infrastructure/postgres/mappers/`](app/infrastructure/postgres/mappers/) |
| **A cache should not own availability** | Project detail caching uses null-cache + resilient cache-aside behavior. | [`app/infrastructure/redis/project_cache.py`](app/infrastructure/redis/project_cache.py) |
| **“Best” is metric-dependent** | Metric directions define maximize/minimize behavior; ignored runs are filtered from ranking. | [`app/application/use_cases/runs/ranking.py`](app/application/use_cases/runs/ranking.py) |
| **Framework wiring should stay at the edge** | `bootstrap.py` connects application ports to concrete infrastructure. | [`app/bootstrap.py`](app/bootstrap.py) |

---

## Can SentinelML do X?

This section is intentionally blunt and searchable.

| I need... | Current answer |
| --- | --- |
| Track **projects, datasets, models, runs, parameters, and metrics** | **Yes** |
| Track dataset and model **versions** | **Yes** |
| Store a **dataset hash**, source, description, and metadata | **Yes** |
| Record run **parameters before execution** | **Yes** — while the run is `waiting` |
| Record run **metrics during execution** | **Yes** — while the run is `running` |
| Compare completed runs using **maximize/minimize** metric semantics | **Yes** |
| Keep a bad run but remove it from ranking | **Yes** — ignore/unignore with a reason |
| Query the best run for a project + metric | **Yes** |
| Use Redis | **Optional at application level**; included in the Docker Compose stack |
| Call SentinelML from external training code | **Yes, through HTTP** |
| A Python SDK or automatic experiment **autologging** | **No** |
| Store model files, plots, checkpoints, logs, or dataset **artifacts** | **No** |
| Stream high-frequency/live training telemetry | **No** |
| Launch training jobs or schedule **GPU** workloads | **No** |
| A model registry or model deployment system | **No** |
| Authentication, users, teams, or workspaces | **No** |
| A rich experiment dashboard | **No** — Swagger UI is the current interface |
| CSV/JSON project-history export | **No dedicated export feature** |
| Built-in code commit, environment, seed, or dependency capture | **No** — these must be recorded manually in available metadata/parameters if desired |
| Horizontal-scale production deployment configuration | **No** |
| Automated tests and CI | **Not yet** |

### Who is this most useful for today?

| Persona | What SentinelML offers | What you still need elsewhere |
| --- | --- | --- |
| **Backend learner / reviewer** | A compact codebase for studying domain rules, Clean Architecture-style boundaries, transactions, row locks, and resilient caching. | Production hardening and automated tests. |
| **Data scientist** | A simple HTTP backend for manually recording experiment context and comparing finished runs. | SDK/autologging, artifacts, plots, and a richer UI. |
| **Researcher** | Versioned dataset/model references, optional dataset hash, parameters, metrics, notes, failure/ignore reasons, and preserved run history. | Full reproducibility still requires code revision, environment, seeds, artifacts, and data lineage practices outside the current system. |
| **MLOps engineer** | A focused reference implementation of experiment-metadata backend concerns. | Auth, workspaces, artifact stores, migrations, observability, deployment/HA, and broader platform integrations. |
| **Large-scale AI/infra team** | The architecture can be inspected as a small bounded example. | Distributed orchestration, GPU scheduling, high-volume telemetry, artifact systems, multi-tenancy, and scale testing are outside the current scope. |

---

## Architecture

SentinelML uses a Clean Architecture-style dependency direction: business behavior points inward; FastAPI, SQLAlchemy, PostgreSQL, and Redis stay at the edges.

```mermaid
flowchart TB
    Client["API client / Swagger"]

    subgraph Presentation["Presentation · FastAPI"]
        Routers["Routers"]
        Schemas["Pydantic schemas"]
        HttpErrors["HTTP error translation"]
    end

    subgraph Application["Application"]
        UseCases["Use cases"]
        Ports["Ports / protocols"]
    end

    subgraph Domain["Domain"]
        Entities["Entities"]
        Rules["Validation + lifecycle rules"]
    end

    subgraph Infrastructure["Infrastructure"]
        Repositories["SQLAlchemy repositories"]
        UoW["Unit of Work"]
        Cache["Redis project cache"]
        Health["Health adapters"]
        Clock["System clock"]
    end

    PG[(PostgreSQL)]
    R[(Redis)]
    Bootstrap["bootstrap.py<br/>composition root"]

    Client --> Routers
    Routers --> Schemas
    Routers --> UseCases
    HttpErrors -. translates .-> Routers

    UseCases --> Entities
    UseCases --> Ports
    Rules --> Entities

    Repositories -. implements .-> Ports
    UoW -. implements .-> Ports
    Cache -. implements .-> Ports
    Health -. implements .-> Ports
    Clock -. implements .-> Ports

    Repositories --> PG
    UoW --> PG
    Cache --> R

    Bootstrap -. wires .-> Routers
    Bootstrap -. constructs .-> Infrastructure
```

### Layers in plain English

| Layer | Job |
| --- | --- |
| **Domain** | Defines what valid entities and run behavior mean. Knows nothing about HTTP, Redis, or SQLAlchemy. |
| **Application** | Coordinates user actions such as “start this run” or “find the best run.” |
| **Infrastructure** | Implements persistence, cache, clock, and health adapters. |
| **Presentation** | Converts HTTP requests into use-case calls and application errors into HTTP responses. |
| **Bootstrap** | Wires abstractions to concrete implementations. |

<details>
<summary><strong>See the transaction + row-locking path</strong></summary>

```mermaid
sequenceDiagram
    participant API as FastAPI router
    participant UC as Application use case
    participant UOW as Unit of Work
    participant Repo as Repository
    participant Domain as Domain entity
    participant DB as PostgreSQL

    API->>UC: command
    UC->>UOW: open transaction scope
    UOW->>Repo: repository access
    Repo->>DB: SELECT ... FOR UPDATE
    DB-->>Repo: locked row
    Repo-->>UC: domain entity
    UC->>Domain: apply business rule
    Domain-->>UC: valid state change
    UC->>Repo: save(entity)
    Repo->>DB: flush changes
    UC->>UOW: commit()
    UOW->>DB: COMMIT
    UC-->>API: result
```

The row lock is targeted at relevant mutation workflows; it is not a global application lock.

</details>

<details>
<summary><strong>See the Redis cache-aside path</strong></summary>

```mermaid
sequenceDiagram
    participant Client
    participant UC as GetProject use case
    participant Cache as Project cache
    participant DB as PostgreSQL

    Client->>UC: GET /projects/{id}
    UC->>Cache: get(project_id)

    alt cache hit
        Cache-->>UC: Project
    else miss or handled Redis failure
        Cache-->>UC: None
        UC->>DB: load project
        DB-->>UC: Project
        UC->>Cache: put(project) · best effort
    end

    UC-->>Client: Project
```

`ResilientProjectCache` converts supported Redis/client/deserialization failures into cache misses on reads. Cache writes and invalidations are best-effort. PostgreSQL remains the durable source of truth.

</details>

---

---

## Data model

The relational model keeps experiment context explicit: runs connect projects, datasets, and models; parameters and metrics belong to runs; metric directions define ranking semantics.

<details>
<summary><strong>Show the entity relationship diagram</strong></summary>

```mermaid
erDiagram
    projects ||--o{ runs : has
    datasets ||--o{ runs : used_by
    models ||--o{ runs : used_by
    runs ||--o{ parameters : has
    runs ||--o{ metrics : logs
    metric_directions ||--o{ metrics : defines

    projects {
        int id PK
        varchar name UK
        text description
    }

    datasets {
        int id PK
        varchar name
        varchar version
        text description
        varchar dataset_hash
        text source
        text metadata
    }

    models {
        int id PK
        varchar name
        varchar version
        text description
        varchar model_type
        text metadata
    }

    runs {
        int id PK
        int project_id FK
        int dataset_id FK
        int model_id FK
        run_status status
        timestamptz start_time
        timestamptz end_time
        boolean is_ignored
        text ignore_reason
        text reason
    }

    parameters {
        int id PK
        int run_id FK
        varchar name
        varchar value
        varchar value_type
        text notes
    }

    metrics {
        int id PK
        int run_id FK
        varchar name FK
        double value
        text notes
    }

    metric_directions {
        varchar name PK
        boolean maximize
    }
```

</details>

PostgreSQL also enforces important integrity below the API layer, including unique project names, unique dataset/model version pairs, unique parameter and metric names within a run, foreign keys, metric-direction references, and the run-status enum.

Schema: [`sql/database.sql`](sql/database.sql)

---

## Developing SentinelML

### Useful commands

```bash
make help
make start
make lint
make format
make up
make build
make down
make clean
make ps
make shapp
```

### “Where do I change X?”

| I want to change... | Start here |
| --- | --- |
| A business invariant or entity rule | `app/domain/` |
| A workflow such as start/complete/rank | `app/application/use_cases/` |
| An abstraction needed by application code | `app/application/ports/` |
| PostgreSQL query/persistence behavior | `app/infrastructure/postgres/` |
| Redis caching behavior | `app/infrastructure/redis/` |
| HTTP request/response shape | `app/presentation/api/` |
| Dependency wiring | `app/bootstrap.py` |
| Environment-backed configuration | `app/config.py` |

### Recommended code-reading path

1. [`app/domain/runs.py`](app/domain/runs.py) — lifecycle and invariants.
2. [`app/application/use_cases/runs/lifecycle.py`](app/application/use_cases/runs/lifecycle.py) — application orchestration.
3. [`app/application/ports/unit_of_work.py`](app/application/ports/unit_of_work.py) — transaction abstraction.
4. [`app/infrastructure/postgres/unit_of_work.py`](app/infrastructure/postgres/unit_of_work.py) — SQLAlchemy implementation.
5. [`app/infrastructure/postgres/repositories/runs.py`](app/infrastructure/postgres/repositories/runs.py) — persistence, locks, ranking queries.
6. [`app/infrastructure/redis/project_cache.py`](app/infrastructure/redis/project_cache.py) — resilient caching.
7. [`app/bootstrap.py`](app/bootstrap.py) — composition root.
8. [`app/presentation/api/routers/runs.py`](app/presentation/api/routers/runs.py) — HTTP edge.

### Project map

```text
app/
├── domain/            # Framework-independent entities and business rules
├── application/
│   ├── exceptions/    # Application-level errors
│   ├── ports/         # Repository, cache, clock, health, and UoW protocols
│   └── use_cases/     # Application workflows
├── infrastructure/
│   ├── postgres/      # SQLAlchemy ORM, mappers, repositories, UoW, health
│   ├── redis/         # Project cache and Redis health adapter
│   └── clock.py       # Concrete system clock
├── presentation/
│   └── api/           # FastAPI routers, schemas, HTTP error translation
├── bootstrap.py       # Composition root / dependency wiring
├── config.py          # Environment-backed settings
└── main.py            # FastAPI application
```

---

## Current maturity

SentinelML is a focused learning/portfolio backend. Its scope is intentionally smaller than a production experiment-management platform.

| Area | Current state |
| --- | --- |
| Domain lifecycle rules | Implemented |
| PostgreSQL constraints + transactions | Implemented |
| Row locking for relevant mutation paths | Implemented |
| Redis project cache + graceful runtime fallback | Implemented |
| Docker Compose local stack | Implemented |
| OpenAPI / Swagger UI | Implemented |
| Authentication / authorization | Not implemented |
| Users / teams / workspaces | Not implemented |
| Artifact storage | Not implemented |
| Database migration framework | Not implemented |
| Pagination / filtering | Not implemented |
| Automated tests | Not implemented |
| CI/CD | Not implemented |
| Production deployment / HA configuration | Not implemented |
| Rich monitoring / tracing / metrics | Not implemented beyond health endpoints |

> [!IMPORTANT]
> Because authentication is not implemented, the current API should not be treated as a production-ready service to expose publicly.

### Natural next steps

1. Add domain and application unit tests.
2. Add PostgreSQL/Redis integration tests and API tests.
3. Add CI for linting, tests, and container builds.
4. Add a database migration workflow.
5. Add pagination, filtering, and sorting.
6. Add authentication and workspace ownership.
7. Add export and artifact metadata/storage integrations.
8. Add an optional client SDK/autologging integration.

---

## Tech stack

| Technology | Role |
| --- | --- |
| **Python 3.12** | Application language |
| **FastAPI** | HTTP API + OpenAPI/Swagger interface |
| **Pydantic 2** | Request and response validation |
| **SQLAlchemy 2** | PostgreSQL persistence implementation |
| **psycopg 3** | PostgreSQL driver |
| **PostgreSQL 16** | Durable data, constraints, transactions, row locking |
| **Redis 8** | Optional project-detail cache |
| **uv** | Dependency and environment management |
| **Ruff** | Linting and formatting |
| **Docker Compose** | Local API + PostgreSQL + Redis stack |

---

## Why this project exists

SentinelML is built around one backend-learning question:

> **What happens when a small CRUD-style API starts getting real business rules?**

The answer introduces state transitions, transaction boundaries, concurrent writes, domain modeling, repository abstractions, infrastructure failures, cache consistency, and trade-offs between simplicity and separation of concerns.

The product scope stays deliberately small so those decisions can be followed end to end.

