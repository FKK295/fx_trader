# Stage 1: Builder
FROM python:3.10-slim as builder

WORKDIR /app

# Install system dependencies required for Python packages and TA-Lib build
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    wget \
    unzip \
    automake \
    libtool \
    libtool-bin \
    pkg-config \
    # For psycopg2-binary
    libpq-dev \
 && rm -rf /var/lib/apt/lists/*

# Build and install TA-Lib from source (v0.4.0)
RUN wget https://github.com/TA-Lib/ta-lib/releases/download/v0.4.0/ta-lib-0.4.0-src.tar.gz \
    && tar -xzf ta-lib-0.4.0-src.tar.gz \
    && cd ta-lib/ \
    # Configure with optimizations and disable unnecessary features
    && ./configure --prefix=/usr \
        --disable-dependency-tracking \
        --enable-static=no \
        --enable-shared=yes \
    # Build with single thread to avoid race conditions
    && make \
    && make install \
    && cd .. \
    && rm -rf ta-lib ta-lib-0.4.0-src.tar.gz \
    # Clear ldconfig cache and update library paths
    && ldconfig

# Set comprehensive environment variables for TA-Lib build/linking
ENV CFLAGS="-I/usr/include/ta-lib -I/usr/include"
ENV LDFLAGS="-L/usr/lib"
ENV LD_LIBRARY_PATH="/usr/lib:${LD_LIBRARY_PATH}"
ENV LIBRARY_PATH="/usr/lib"

# Create symlinks for compatibility with different naming conventions
RUN if [ ! -f /usr/lib/libta_lib.so ] && [ -f /usr/lib/libta-lib.so ]; then \
        ln -s /usr/lib/libta-lib.so /usr/lib/libta_lib.so; \
    fi && \
    if [ ! -f /usr/lib/libta_lib.so.0 ] && [ -f /usr/lib/libta-lib.so.0 ]; then \
        ln -s /usr/lib/libta-lib.so.0 /usr/lib/libta_lib.so.0; \
    fi

# Install Poetry
ENV POETRY_VERSION=1.7.1
ENV POETRY_HOME="/opt/poetry"
ENV PATH="$POETRY_HOME/bin:$PATH"

# Install Poetry
RUN pip install "poetry==$POETRY_VERSION"

# Configure Poetry
RUN poetry config virtualenvs.create false \
    && poetry config cache-dir /tmp/poetry-cache

# Copy only requirements files first to leverage Docker cache
COPY pyproject.toml ./

# Generate poetry.lock in the container's environment
RUN poetry lock --no-update --no-interaction

# Install production dependencies only
RUN poetry install --only main --no-interaction --no-ansi --no-root

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

# Install runtime system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgomp1 \
    # For psycopg2-binary (if needed)
    libpq5 \
    && rm -rf /var/lib/apt/lists/* \
    && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# Copy TA-Lib shared libraries
COPY --from=builder /usr/lib/libta-lib.* /usr/lib/
COPY --from=builder /usr/include/ta-lib /usr/include/ta-lib/
RUN ldconfig

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