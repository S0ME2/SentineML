# Setup

[README](../README.md) / Setup

Use Docker Compose for the complete local stack. Native Python setup is useful
when developing the API or connecting to a PostgreSQL instance you manage.

## Docker Compose

### Start the workspace

Install Docker and Docker Compose **2.24 or newer**, then run these commands from
the repository root:

```sh
docker compose up -d --build --wait
docker compose ps
curl --fail --silent --show-error http://127.0.0.1:8888/health/db
```

The last command should return `{"status":"ok"}`. Open the
[dashboard](http://127.0.0.1:8888/ui/) or
[interactive API docs](http://127.0.0.1:8888/docs).

The default configuration is in [.env.docker.example](../.env.docker.example).
Only the application port is published, on `127.0.0.1`. PostgreSQL and Redis
remain on the internal Docker network.

### Change the port

```sh
APP_PORT=8889 docker compose up -d --build --wait
```

Open `http://127.0.0.1:8889/ui/`. Point scripts at the same address:

```sh
python3 -m examples.track_experiment --url http://127.0.0.1:8889
```

The optional example requires Python 3.12 or newer on the host.

### Override configuration

Create an ignored `.env.local.docker` file to override the checked-in defaults.
For example, before starting a new database:

```dotenv
POSTGRES_USER=sentinelml
POSTGRES_PASSWORD=your-chosen-password
POSTGRES_DB=sentinelml
DATABASE_URL=postgresql://sentinelml:your-chosen-password@db:5432/sentinelml
REDIS_URL=redis://redis:6379/0
PROJECT_CACHE_TTL_SECONDS=300
```

Use the same database password in `POSTGRES_PASSWORD` and `DATABASE_URL`;
URL-encode special characters in the URL. Changing this file does **not** change
the password of an already initialized PostgreSQL database.

| Setting | Purpose |
| --- | --- |
| `DATABASE_URL` | PostgreSQL connection used by the application; required |
| `REDIS_URL` | Optional project cache; empty disables it in the application |
| `PROJECT_CACHE_TTL_SECONDS` | Positive integer cache lifetime; default `300` |
| `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB` | Initialize the Compose database on first startup |
| `APP_PORT` | Host HTTP port, set in the shell or Compose's `.env`; default `8888` |

`.env.local.docker` configures container environments, not Compose port
interpolation. Use the shell command above to change `APP_PORT`.

### Stop and restart

```sh
docker compose down
docker compose up -d --wait
```

`down` removes containers and the network, but keeps named volumes. The second
command reuses the stored data. After pulling code changes, check the
[release policy](RELEASES.md) before rebuilding against an existing database.

## Back up your history

With the Compose database running, create a PostgreSQL custom-format dump:

```sh
make backup
```

The command prints the path under `backups/` and refuses to overwrite an existing
file. Keep dumps private: they contain the full experiment database. Backups are
ignored by Git. Test recovery in an isolated PostgreSQL 16 instance running the
same SentinelML version; see [backup and upgrade guidance](RELEASES.md#schema-and-upgrades).

CSV and JSON exports contain run rows and basic metadata, not the full database.

## Native Python

You need Python **3.12**, uv, and a separately provisioned PostgreSQL **16** database
with a role allowed to create tables. Redis is optional. The provided Compose
stack does not publish its database port, so it is not a host database connection
for native development.

1. Install the locked Python dependencies:

   ```sh
   uv sync --locked
   ```

2. Copy [.env.example](../.env.example) to `.env.local` and replace its connection
   placeholders with your own PostgreSQL role and **empty** database:

   ```sh
   cp .env.example .env.local
   ```

3. Initialize that database. Export the same connection URL in your shell for
   `psql`; it does not load `.env.local` automatically:

   ```sh
   export DATABASE_URL='postgresql://USER:PASSWORD@localhost:5432/DBNAME'
   psql "$DATABASE_URL" -v ON_ERROR_STOP=1 -f sql/database.sql
   ```

   Replace the placeholders before running. Use your normal secret-management
   practice when entering credentials. Initialization creates a new schema in a
   transaction and refuses existing objects. It is not a reset or migration.

4. Start the application:

   ```sh
   make start
   ```

   The application reads `.env.local`; exported variables take precedence. Open
   `http://127.0.0.1:8888/ui/`. `make start` uses reload mode for development.

## Troubleshooting

| Symptom | Check or action |
| --- | --- |
| Compose rejects `required: false` | Upgrade Compose to 2.24 or newer. The optional override file uses that feature. |
| Port `8888` is busy | Set `APP_PORT` to an unused port and use that port in the browser and scripts. |
| App or database fails to start | Run `docker compose logs --tail=100 app db redis`. Check credentials, connection URL, and health output. |
| Redis is unhealthy | The supplied Compose stack waits for Redis. The native application can run without it when `REDIS_URL` is empty. |
| Native app reports a missing `DATABASE_URL` | Check `.env.local`, the current working directory, and exported environment variables. |
| A schema change is absent | Initialization SQL runs only when creating an empty database volume; it does not upgrade existing tables. |
| `/health/` is OK but operations fail | Check `/health/db`. `/health/` only confirms that the API process is responding. |

Health endpoints return a JSON `status`; inspect that value as well as the HTTP
status. Redis health returns `error` when Redis is disabled or unavailable.

### Reset a disposable database

Only use this when you intend to erase the current Compose project's experiment
history. Back up anything you want to keep first.

```sh
make clean CONFIRM=YES
make build
```

`make clean` removes PostgreSQL **and** Redis volumes. For trying another schema
without erasing your workspace, start a separate Compose project as described in
[the release policy](RELEASES.md#schema-and-upgrades).

For remote access, use [the HTTPS gateway guide](DEPLOYMENT.md).
