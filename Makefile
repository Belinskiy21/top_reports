.PHONY: fix check watch test seed serve

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
	$(PYTHON) db/seed.py

serve:
	$(PYTHON) -m uvicorn app.main:app --host 127.0.0.1 --port 8000

watch:
	watchfiles "make check" .
