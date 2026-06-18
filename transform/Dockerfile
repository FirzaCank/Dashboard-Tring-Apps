FROM python:3.12-slim

WORKDIR /app

RUN pip install --no-cache-dir dbt-bigquery==1.8.2

COPY . .

RUN useradd -m dbtuser
USER dbtuser

ENTRYPOINT ["dbt"]
