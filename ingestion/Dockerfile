FROM python:3.12-slim

WORKDIR /app

COPY pyproject.toml ./

RUN pip install --no-cache-dir \
    "google-cloud-bigquery>=3.20" \
    "google-cloud-secret-manager>=2.20" \
    "requests>=2.32" \
    "tenacity>=8.3"

COPY src/ ./src/

RUN useradd -m appuser
USER appuser

ENV PYTHONPATH=/app/src

ENTRYPOINT ["python", "-m", "tring_ingest"]
