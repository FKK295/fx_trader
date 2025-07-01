#!/bin/bash
set -e # Exit immediately if a command exits with a non-zero status.

# Default to "api" if no command is provided
COMMAND=${1:-api}

echo "Docker Entrypoint: Received command '$COMMAND'"

# Activate virtual environment if Poetry created one and it was copied
# (Though `poetry config virtualenvs.create false` in Dockerfile builder stage
# means dependencies are installed globally in the Python site-packages of the image)

# Common setup tasks can go here
# For example, waiting for database to be ready (if applicable and not handled by docker-compose healthchecks)
# echo "Running database migrations..."
# poetry run alembic upgrade head # If using Alembic for DB migrations

if [ "$COMMAND" = "api" ]; then
  echo "Starting FastAPI application..."
  # Ensure FX_TRADER_APP_MODULE is set, e.g., fx_trader.app.main:app
  
  # Default to no reload for production
  RELOAD_OPTION=""
  
  # Enable reload only if UVICORN_RELOAD is explicitly set to "true"
  if [ "${UVICORN_RELOAD:-false}" = "true" ]; then
    echo "Hot reload enabled (development mode)"
    RELOAD_OPTION="--reload"
  fi
  
  # Execute uvicorn with the appropriate options
  exec uvicorn \
    ${FX_TRADER_APP_MODULE:-fx_trader.app.main:app} \
    --host 0.0.0.0 \
    --port ${PORT:-8000} \
    $RELOAD_OPTION
elif [ "$COMMAND" = "worker" ]; then
  echo "Starting Celery worker..."
  # Ensure FX_TRADER_CELERY_APP is set, e.g., fx_trader.app.celery_app:app
  exec celery -A ${FX_TRADER_CELERY_APP:-fx_trader.app.celery_worker.celery_app} worker -l INFO --concurrency=${CELERY_CONCURRENCY:-4}
elif [ "$COMMAND" = "scheduler" ]; then # For Celery Beat or other schedulers
  echo "Starting Celery Beat scheduler..."
  exec celery -A ${FX_TRADER_CELERY_APP:-fx_trader.app.celery_worker.celery_app} beat -l INFO --scheduler django_celery_beat.schedulers:DatabaseScheduler # Example
elif [ "$COMMAND" = "train" ]; then
  echo "Running training script..."
  exec python -m fx_trader.mlops.train "$@" # Pass additional args
elif [ "$COMMAND" = "backtest" ]; then
  echo "Running backtest script..."
  exec python -m fx_trader.backtest.runner "$@" # Pass additional args
else
  echo "Unknown command: $COMMAND"
  echo "Available commands: api, worker, scheduler, train, backtest"
  echo "Or executing command directly: $@"
  exec "$@" # Allow running arbitrary commands
fi