#!/bin/sh
set -e

# Initialize Redis command arguments
REDIS_CMD_ARGS="--save 60 1 --loglevel warning"

# Add requirepass if REDIS_PASSWORD is set
if [ -n "$REDIS_PASSWORD" ]; then
    echo "Configuring Redis with password authentication"
    REDIS_CMD_ARGS="$REDIS_CMD_ARGS --requirepass $REDIS_PASSWORD"
else
    echo "Starting Redis without password authentication"
fi

# Execute Redis server with the configured arguments
echo "Starting Redis with arguments: $REDIS_CMD_ARGS"
exec redis-server $REDIS_CMD_ARGS
