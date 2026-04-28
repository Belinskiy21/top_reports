.PHONY: fix check watch test seed infra prefetch-bootstrap worker beat serve

PYTHON ?= $(if $(wildcard .venv/bin/python),.venv/bin/python,python3)

fix:
	$(PYTHON) -m ruff check . --fix
	$(PYTHON) -m ruff format .

check:
	$(PYTHON) -m ruff check .
	$(PYTHON) -m ruff format --check .
	$(PYTHON) -m basedpyright
	$(PYTHON) -m mypy .

test:
	$(PYTHON) -m pytest -q

seed:
	$(PYTHON) -m db.seed

infra:
	docker compose up -d db redis

prefetch-bootstrap:
	$(PYTHON) -m app.bootstrap_prefetch

worker:
	$(PYTHON) -m celery -A app.celery_app.celery_app worker --loglevel=info

beat:
	$(PYTHON) -m celery -A app.celery_app.celery_app beat --loglevel=info

serve:
	$(PYTHON) scripts/serve_local.py

watch:
	watchfiles "make check" .
