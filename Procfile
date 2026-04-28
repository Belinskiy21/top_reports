web: /app/docker/entrypoint.sh
prefetch_bootstrap: python -m app.bootstrap_prefetch
worker: celery -A app.celery_app.celery_app worker --loglevel=info
beat: celery -A app.celery_app.celery_app beat --loglevel=info
