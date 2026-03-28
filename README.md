# Top Reports API

Small FastAPI service backed by PostgreSQL and SQLAlchemy.

## Requirements

- Python 3.14 for local development in this repo
- PostgreSQL 14+ available locally or remotely
- Docker and Docker Compose, if you want to run the full stack in containers

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

### 3. Start PostgreSQL

Make sure you have a running PostgreSQL instance and that the connection variables point to it.

Example:

```bash
export PGUSER=postgres
export PGPASSWORD=postgres
export PGHOST=127.0.0.1
export PGPORT=5432
export PGDATABASE=top_reports
```

### 4. Initialize the database schema

```bash
python db/seed.py
```

This creates the target database if it does not already exist and then creates the `users` table.

### 5. Start the API

```bash
make serve
```

The app will be available at `http://127.0.0.1:8000`.

### 6. Verify

```bash
make test
make check
```

## Run With Docker Compose

The repo includes `docker-compose.yml` with two services:

- `db`: PostgreSQL 16
- `app`: FastAPI app built from the local `Dockerfile`

The app waits for Postgres, runs `python db/seed.py`, and then starts Uvicorn.

### 1. Start the stack

```bash
docker compose up --build
```

This starts:

- PostgreSQL on `localhost:5432`
- FastAPI on `http://127.0.0.1:8000`

### 2. Verify

```bash
make test
make check
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

## API Docs

- Common endpoints: [docs/api/common.md](/Users/olehpro/work/tasks/quartr/top_reports/docs/api/common.md)
- Versioned endpoints: [docs/api/v1.md](/Users/olehpro/work/tasks/quartr/top_reports/docs/api/v1.md)

## Notes

- The base container entrypoint in `docker/entrypoint.sh` starts only the web server.
- `docker-compose.yml` overrides the container command so the app seeds the database before starting.
- The Docker image and local project configuration both target Python 3.14.
