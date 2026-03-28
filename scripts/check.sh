#!/usr/bin/env bash
set -e

echo "Running ruff..."
python -m ruff check . --fix

echo "Running ruff format check..."
python -m ruff format --check .

echo "Running basedpyright..."
python -m basedpyright

echo "Running mypy..."
python -m mypy .