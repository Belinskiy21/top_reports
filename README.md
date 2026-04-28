# Top Reports API

FastAPI service for authenticated access to recent SEC company reports.
It supports user sign-up/sign-in with JWT auth, serves cached SEC report PDFs for selected companies, stores generated files locally or in S3, and tracks generated report metadata and download history in PostgreSQL via SQLAlchemy.
SEC metadata fetching and PDF generation now run in Celery background processes backed by Redis.

## Requirements

- Python 3.14 for local development in this repo
- PostgreSQL 14+ available locally or remotely
- Docker and Docker Compose, if you want to run the full stack in containers

Use [.env.example](.env.example) as the reference list of supported environment variables and default development values.

Background report prefetch is part of the default architecture:

- `SEC_USER_AGENT` should be set to a real app-level contact string like `top-reports sec-contact@your-domain.com`; generic values such as `quartr` may be rejected by SEC with `403`
- `CELERY_BROKER_URL` configures the broker, default `redis://redis:6379/0`
- `CELERY_RESULT_BACKEND` defaults to the same Redis instance
- `CELERY_TIMEZONE` controls Celery Beat schedule interpretation, default `UTC`
- `REPORT_PREFETCH_USER_EMAIL` selects which app user is recorded as the creator of prefetched report rows

Celery Beat runs the periodic schedule, Celery Worker executes the jobs, and a one-shot bootstrap process performs the initial warm-up on stack boot. The API request path is cache-only and does not call SEC directly. The default schedule currently refreshes `10-K` daily at `03:00` in the configured Celery timezone.

The app reads database settings from `DATABASE_URL` or from standard Postgres variables:

- `PGUSER`
- `PGPASSWORD`
- `PGHOST`
- `PGPORT`
- `PGDATABASE`

If none are set, the app defaults to:

```text
PGUSER=<your current OS user>
PGPASSWORD=
PGHOST=localhost
PGPORT=5432
PGDATABASE=top_reports
```

## Run Without Docker

### 1. Create and activate a virtual environment

```bash
python3.14 -m venv .venv
source .venv/bin/activate
```

### 2. Install dependencies

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip install -r requirements-dev.txt
```

### 2.1 Environment variables

Review [.env.example](.env.example) and export the values you need for your environment.

For local setup, a common pattern is:

```bash
cp .env.example .env
```

### 3. Start local infrastructure

`make serve` expects PostgreSQL to already be reachable on the configured host and port. The simplest local setup is to start Postgres and Redis from Docker Compose first:

```bash
make infra
```

If you prefer to run PostgreSQL yourself instead of Docker Compose, make sure it is running and that the connection variables point to it.

Example:

```bash
export PGUSER=$(whoami)
export PGPASSWORD=
export PGHOST=127.0.0.1
export PGPORT=5432
export PGDATABASE=top_reports
```

### 4. Initialize the database schema

```bash
python -m db.seed
```

This creates the target database if it does not already exist, creates the app tables, and seeds a demo user.
It also seeds the supported companies registry used by the SEC report flow:

- Apple
- Meta
- Alphabet
- Amazon
- Netflix
- Goldman Sachs

Set `SEC_USER_AGENT` to a real app-level contact string so SEC does not reject the background prefetch requests.

### 5. Start local processes

```bash
make serve
```

`make serve` now seeds the database, prints the seeded user credentials and token, runs the one-shot startup prefetch, and then starts the API. If PostgreSQL is not reachable, it exits with a short actionable message instead of a long stack trace.

Typical local startup:

```bash
make infra
make serve
```

For the full local architecture, also start the worker and beat in separate terminals:

```bash
make worker
make beat
```

The API will be available at `http://127.0.0.1:8000`.

### 6. Verify

```bash
make test
make check
```

## Run With Docker Compose

The repo includes `docker-compose.yml` with seven services:

- `db`: PostgreSQL 16
- `redis`: Redis broker/backend for Celery
- `seed`: one-shot database and seeded-user initializer
- `app`: FastAPI app built from the local `Dockerfile`
- `prefetch_bootstrap`: one-shot startup warm-up process
- `worker`: Celery worker that runs SEC prefetch tasks
- `beat`: Celery Beat scheduler that dispatches recurring prefetch tasks

The `seed` service runs `python -m db.seed` once. The app, bootstrap, worker, and beat services wait for that initialization to complete before starting.

### 1. Start the stack

On the host machine, create a local env file first if you have not already:

```bash
cp .env.example .env
```

Then update `.env` with a real SEC contact user agent, for example:

```bash
SEC_USER_AGENT=top-reports sec-contact@your-domain.com
```

Then start the containers from the host machine:

```bash
docker compose up --build
```

Docker Compose uses the internal `db` hostname for the app container automatically. You do not need to set a container-specific `DATABASE_URL` in `.env` for this flow.

To read the seeded JWT after startup, inspect the app container logs:

```bash
docker compose logs app
```

This starts:

- PostgreSQL on `localhost:5432`
- Redis on the internal `redis:6379` network address
- FastAPI on `http://127.0.0.1:8000`
- one startup warm-up pass through `prefetch_bootstrap`
- Celery worker and Celery Beat for ongoing automatic report warming

### 2. Verify

```bash
make test
make check
```

With Docker Compose, the app is already started by the `app` service, so you do not run `make serve` separately. `make serve` is only for the local non-Docker flow above.

If you want to run project commands inside the already running app container:

```bash
docker compose exec app make seed
docker compose exec app make test
docker compose exec app make check
```

### 3. Stop the stack

```bash
docker compose down
```

To remove the Postgres data volume as well:

```bash
docker compose down -v
```

## Useful Commands

```bash
make serve   # seed, prefetch once, then run uvicorn locally
make infra   # start only postgres and redis with docker compose
make worker  # run celery worker locally
make beat    # run celery beat locally
make test    # run pytest
make check   # run ruff, basedpyright, mypy
make fix     # auto-fix and format with ruff
make seed    # create database and schema
```

## User Flow

Running `python -m db.seed` creates or refreshes a demo user and prints its credentials to the terminal.

Seeded user:

- email: `seeded-user@quartr.dev`
- password: `seeded-password`
- token: generated fresh on each seed run and valid for 24 hours

Typical flow:

1. Run `python -m db.seed`
2. Copy the printed token from the seed output, or get a token through `POST /api/v1/sign-up` or `POST /api/v1/sign-in`
3. Call `POST /api/v1/get-report-urls` with `Authorization: Bearer <token>`
4. Use the returned file URL to download the generated PDF

The API only serves cached reports. `prefetch_bootstrap` performs one startup warm-up pass, and Celery Beat schedules periodic refresh jobs afterward. Those background jobs refresh the latest supported report for each seeded company and keep only the newest stored PDF per company/report type.

If you use the seeded token printed by `python -m db.seed`, the sign-in request is optional.

Sign up a new user:

```bash
curl -X POST http://127.0.0.1:8000/api/v1/sign-up \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "super-secret"
  }'
```

Sign in with the seeded user:

```bash
curl -X POST http://127.0.0.1:8000/api/v1/sign-in \
  -H "Content-Type: application/json" \
  -d '{
    "email": "seeded-user@quartr.dev",
    "password": "seeded-password"
  }'
```

Request report URLs:

```bash
curl -X POST http://127.0.0.1:8000/api/v1/get-report-urls \
-H "Authorization: Bearer <jwt-token>" \
  -H "Content-Type: application/json" \
  -d '{
    "report_type": "10-K",
    "companies": ["Apple", "Meta"]
  }'
```

Download a generated PDF:

```bash
curl -L "<file-url-from-get-report-urls>" \
  -H "Authorization: Bearer <jwt-token>" \
  --output apple_report.pdf
```

With `STORAGE_BACKEND=local`, that file URL points back to `GET /api/v1/files/{file_name}` on this API.
With `STORAGE_BACKEND=s3`, `POST /api/v1/get-report-urls` can return a direct object URL instead.

## API Docs

- Common endpoints: [docs/api/common.md](docs/api/common.md)
- Versioned endpoints: [docs/api/v1.md](docs/api/v1.md)

- `docker-compose.yml` overrides the container command so the app seeds the database before starting.
- The Docker image and local project configuration both target Python 3.14.
