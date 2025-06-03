# Stage 1: Builder
FROM python:3.10-slim as builder

WORKDIR /app

# Install system dependencies required for Python packages
# TA-Lib is a common one. Add others if your dependencies need them.
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libta-lib-dev \
    # Add other system dependencies here if needed by your Python packages
    # For example, for psycopg2 (if not using -binary) or other C extensions
    # libpq-dev
 && rm -rf /var/lib/apt/lists/*

# Install Poetry
ENV POETRY_VERSION=1.7.1 # Pin Poetry version for reproducibility
RUN pip install "poetry==$POETRY_VERSION"

# Configure Poetry to not create virtualenvs within the project directory
RUN poetry config virtualenvs.create false

# Copy only files necessary for dependency installation
COPY pyproject.toml poetry.lock ./

# Install dependencies (excluding dev dependencies)
# --no-root: Do not install the project itself yet, only dependencies
RUN poetry install --no-dev --no-interaction --no-ansi --no-root


# Stage 2: Runner
FROM python:3.10-slim as runner

WORKDIR /app

# Create a non-root user and group
ARG UID=10001
RUN adduser \
    --disabled-password \
    --gecos "" \
    --home "/nonexistent" \
    --shell "/sbin/nologin" \
    --no-create-home \
    --uid "${UID}" \
    appuser

# Install system dependencies needed at runtime (e.g., TA-Lib runtime library)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libta-lib0 \
    # libpq5 # For psycopg2-binary runtime if needed, though binary usually includes it
 && rm -rf /var/lib/apt/lists/*

# Copy installed dependencies from builder stage
COPY --from=builder /usr/local/lib/python3.10/site-packages /usr/local/lib/python3.10/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY . .

# Ensure scripts are executable
RUN chmod +x /app/docker-entrypoint.sh

# Switch to non-root user
USER appuser

# Set entrypoint
ENTRYPOINT ["/app/docker-entrypoint.sh"]

# Default command (can be overridden in docker-compose.yml)
CMD ["api"]