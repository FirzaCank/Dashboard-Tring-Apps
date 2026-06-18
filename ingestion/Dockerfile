FROM python:3.12-slim

WORKDIR /app

# Install uv
COPY --from=ghcr.io/astral-sh/uv:0.4.4 /uv /usr/local/bin/uv

# Copy dependency files first for layer caching
COPY pyproject.toml uv.lock ./

# Install production dependencies only (no dev extras)
RUN uv sync --frozen --no-dev

# Copy source
COPY src/ ./src/

# Run as non-root
RUN useradd -m appuser
USER appuser

ENV PYTHONPATH=/app/src

ENTRYPOINT ["uv", "run", "python", "-m", "tring_ingest"]
