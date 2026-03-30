# Top Reports API

FastAPI service for authenticated access to recent SEC company reports.
It supports user sign-up/sign-in with JWT auth, fetches the latest supported SEC filings for selected companies, converts filings to PDF, stores generated files locally or in S3, and tracks generated report metadata and download history in PostgreSQL via SQLAlchemy.

## Requirements

- Python 3.14 for local development in this repo
- PostgreSQL 14+ available locally or remotely
- Docker and Docker Compose, if you want to run the full stack in containers

Use [.env.example](.env.example) as the reference list of supported environment variables and default development values.

The app also supports an optional background prefetch job for SEC reports:

- `REPORT_PREFETCH_ENABLED=true` enables a scheduled cache warm-up loop
- `SEC_USER_AGENT` should be set to a real app-level contact string like `top-reports sec-contact@your-domain.com`; generic values such as `quartr` may be rejected by SEC with `403`
- `REPORT_PREFETCH_INTERVAL_SECONDS` controls how often it runs, default `86400`
- `REPORT_PREFETCH_USER_EMAIL` selects which app user is recorded as the creator of prefetched report rows

This prefetcher exists to reduce cold-request latency when `storage/files` does not already contain generated PDFs. Instead of generating reports only on demand, the app can warm the latest supported filings in the background and keep just the newest PDF per company/report type.

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

### 3. Start PostgreSQL

Make sure you have a running PostgreSQL instance and that the connection variables point to it.

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

If you want the app to keep the latest report PDFs warm in storage and avoid slow first-time report generation, enable `REPORT_PREFETCH_ENABLED=true` in your environment before starting the API. Also set `SEC_USER_AGENT` to a real app-level contact string so SEC does not reject the prefetch requests.

### 5. Start the API

```bash
make serve
```

The app will be available at `http://127.0.0.1:8000`.

Start the API with prefetch enabled:

```bash
REPORT_PREFETCH_ENABLED=true make serve
```

### 6. Verify

```bash
make test
make check
```

## Run With Docker Compose

The repo includes `docker-compose.yml` with two services:

- `db`: PostgreSQL 16
- `app`: FastAPI app built from the local `Dockerfile`

The app waits for Postgres, runs `python -m db.seed`, and then starts Uvicorn.

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
- FastAPI on `http://127.0.0.1:8000`

If `REPORT_PREFETCH_ENABLED=true` is set in `.env`, the app will also start a background prefetch loop on boot. That loop checks SEC metadata on the configured interval, refreshes the latest supported reports, and removes replaced PDFs so only the newest generated file is kept per company/report type.

Start Docker Compose with prefetch enabled without editing `.env`:

```bash
REPORT_PREFETCH_ENABLED=true docker compose up --build
```

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
make serve   # run uvicorn locally
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

If background prefetch is enabled, the app starts that loop when FastAPI boots, not during `python -m db.seed`. The scheduler then refreshes the latest supported report for each seeded company on the configured interval and keeps only the newest stored PDF per company/report type. This is intended to reduce report-generation latency when storage is empty or stale.

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

## API Docs

- Common endpoints: [docs/api/common.md](docs/api/common.md)
- Versioned endpoints: [docs/api/v1.md](docs/api/v1.md)

- `docker-compose.yml` overrides the container command so the app seeds the database before starting.
- The Docker image and local project configuration both target Python 3.14.
