# Contributing Guide

For developers working on this pipeline.

---

## Branch Strategy

Two long-lived branches:

| Branch | Deploys to | Purpose |
|---|---|---|
| `develop` | Dev GCP project | Integration testing, feature verification |
| `main` | Prod GCP project (client) | Live production pipeline |

**Never push directly to `main`.** All changes go through `develop` first.

---

## Development Workflow

```
1. Create feature branch from develop
   git checkout develop
   git pull origin develop
   git checkout -b feature/your-feature

2. Make changes + run local checks
   make test          # 38 tests + dbt parse
   make lint          # ruff

3. Push feature branch + open PR to develop
   git push origin feature/your-feature
   # open PR: feature/* -> develop on GitHub

4. After PR merged to develop:
   - Cloud Build auto-deploys to dev GCP project
   - Run E2E verify on dev environment (see runbook.md §1)
   - Check dbt PASS/ERROR count in Cloud Logging

5. When develop is verified, open PR: develop -> main
   - PR requires review before merge
   - Merge to main triggers Cloud Build deploy to prod GCP
   - NEVER merge directly via git merge — always use PR on GitHub
```

---

## Local Checks (required before PR)

```bash
cd tring-data-pipeline

# install deps
cd ingestion && uv sync --extra dev && cd ..

# lint + format
make lint

# tests (ingestion unit tests + dbt parse)
make test
```

All checks must pass. Pre-commit hooks (ruff, trailing whitespace, detect-secrets) run automatically on `git commit`.

---

## Cloud Build Triggers (set up once by client admin)

| Trigger | Branch | Config file | Target |
|---|---|---|---|
| `deploy-develop` | `develop` | `cloudbuild/deploy-dev.yaml` | Dev GCP |
| `deploy-main` | `main` | `cloudbuild/deploy-prod.yaml` | Prod GCP |

Setup: see `docs/handover.md` Step 4. Requires GitLab connection + VPN access to client GCP.

Until triggers are set up, deploy manually:

```bash
# deploy to dev manually
gcloud builds submit . \
  --config=cloudbuild/deploy-dev.yaml \
  --substitutions=_PROJECT=YOUR_DEV_PROJECT,COMMIT_SHA=latest \
  --project=YOUR_DEV_PROJECT

# deploy to prod manually
gcloud builds submit . \
  --config=cloudbuild/deploy-prod.yaml \
  --substitutions=_PROJECT=YOUR_PROD_PROJECT,COMMIT_SHA=latest \
  --project=YOUR_PROD_PROJECT
```

---

## Commit Message Format

```
<type> <scope> - <short description>

Types: feat, fix, docs, chore, refactor, test
Scope: ingestion, transform, orchestration, infra, docs

Examples:
  feat ingestion - add new appsflyer endpoint
  fix transform - handle null values in mart_appsflyer
  docs - update runbook backfill section
  chore orchestration - bump workflow retry count
```

No `Co-authored-by` lines. No conventional commit prefixes with colon (`feat:` not allowed — use `feat scope - desc`).

---

## Environment Variables

Never hardcode credentials. All secrets via Secret Manager or `.env` (gitignored).

```bash
# local .env (never commit)
APPSFLYER_API_TOKEN=...
MOENGAGE_API_CREDS=...
PLAY_CONSOLE_SECRET_NAME=...
APPSTORE_KEY_ID=...
APPSTORE_ISSUER_ID=...
APPSTORE_P8_PATH=...
GCP_PROJECT=...
```

---

## Adding a New Data Source or Endpoint

See `docs/adding-endpoints.md` for step-by-step guide.
