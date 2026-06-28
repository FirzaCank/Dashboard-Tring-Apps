# Data Catalog: App Store Connect Raw Layer

Status: **IN PROGRESS (2026-06-26)** - Auth working, code scaffold done, GCP infra not yet provisioned. Analytics instances pending (Apple generates 24-48h after first request created 2026-06-26).

---

## Overview

| Data Type | BQ Table (planned) | Source API | Notes |
|---|---|---|---|
| App analytics (installs, sessions, downloads, engagement) | `appstore_raw.raw_analytics_*` | Analytics Reports API | Async 4-step flow, gzip TSV |
| Customer reviews | `appstore_raw.raw_reviews` | App Store Connect v1 API | Synchronous JSON, paginated |
| Sales reports | `appstore_raw.raw_sales` | Sales Reports API | Requires vendor number, gzip TSV |
| Finance reports | `appstore_raw.raw_finance` | Finance Reports API | Requires vendor number, gzip TSV |

---

## API Details

| Field | Value |
|---|---|
| Base URL | `https://api.appstoreconnect.apple.com` |
| Auth | ES256 JWT, signed with .p8 private key |
| Key ID | `3JJKJT5QCK` (from `.env`, never hardcode) |
| Issuer ID | `69a6de96-4e47-47e3-e053-5b8c7c11a4d1` (from `.env`) |
| .p8 file | `AuthKey_3JJKJT5QCK.p8` at repo root (gitignored) |
| Secret name | `appstore-connect-key` (stores .p8 content, created during GCP setup) |
| App ID | `1350501409` |
| Bundle ID | `com.pegadaian.digital` |
| JWT expiry | 20 minutes max (Apple limit) |

### JWT generation

```python
import time, jwt
from pathlib import Path

KEY_ID = os.environ["APPSTORE_KEY_ID"]
ISSUER_ID = os.environ["APPSTORE_ISSUER_ID"]
p8 = Path(os.environ["APPSTORE_P8_PATH"]).read_text().strip()

now = int(time.time())
token = jwt.encode(
    {"iss": ISSUER_ID, "iat": now, "exp": now + 1200, "aud": "appstoreconnect-v1"},
    p8,
    algorithm="ES256",
    headers={"kid": KEY_ID},
)
```

---

## Analytics Reports API (no vendor number needed)

> **Important:** This API is async, NOT a simple GET. You POST a request, Apple generates report files on their side (24-48h for first generation), then you download gzip TSV files. After the first generation, ONGOING requests produce new daily instances automatically.

### Step 1 - Create report request

**1a. ONGOING (daily pipeline — POST sekali, reuse selamanya)**

```
POST /v1/analyticsReportRequests
Body: {
  "data": {
    "type": "analyticsReportRequests",
    "attributes": {"accessType": "ONGOING"},
    "relationships": {"app": {"data": {"type": "apps", "id": "1350501409"}}}
  }
}
```

Returns `request_id`. Reuse setiap hari — Apple auto-generate instance baru tiap hari.

**Active ONGOING request (created 2026-06-26):** `77203237-b1c3-40ed-bccf-ce4345c7d5ab`

**1b. ONE_TIME_SNAPSHOT (backfill historis 2024-2025 — POST sekali, tunggu 24-48h)**

```
POST /v1/analyticsReportRequests
Body: {
  "data": {
    "type": "analyticsReportRequests",
    "attributes": {"accessType": "ONE_TIME_SNAPSHOT"},
    "relationships": {"app": {"data": {"type": "apps", "id": "1350501409"}}}
  }
}
```

Apple generate semua data historis yang tersedia (~1-2 tahun ke belakang) dalam satu batch.
Batas: **1 snapshot per bulan per app**. Instance tersedia 35 hari setelah dibuat.

```bash
# Jalankan snapshot via test script:
cd tring-data-pipeline
uv run --with PyJWT --with cryptography --with requests python3 ../test-appstore/test_appstore_endpoints.py --snapshot
```

### Step 2 - List available reports

```
GET /v1/analyticsReportRequests/{request_id}/reports?limit=200
```

Returns 156 report types. Dashboard-relevant categories:

| Category | Count | Key reports for dashboard |
|---|---|---|
| `APP_USAGE` | 15 | App Store Installation and Deletion Standard, App Sessions Standard |
| `COMMERCE` | 10 | App Downloads Standard, App Store Purchases Standard |
| `APP_STORE_ENGAGEMENT` | 5 | App Store Discovery and Engagement Standard |
| `PERFORMANCE` | 23 | App Install Performance |
| `FRAMEWORK_USAGE` | 103 | Not needed for dashboard |

Each report has a stable `report_id` per request (format: `r{N}-{request_id}`).

### Step 3 - Get instances (check daily)

```
GET /v1/analyticsReports/{report_id}/instances?limit=10
```

Returns available data files. Each instance has:
- `granularity`: `DAILY` or `MONTHLY`
- `processingDate`: when Apple generated the file
- `size`: file size in bytes

Empty = Apple still generating (check again next day). Once populated, new instances appear daily for ONGOING requests.

### Step 4 - Get download segments

```
GET /v1/analyticsReportInstances/{instance_id}/segments
```

Returns download URLs (pre-signed S3-style, time-limited). Each segment has:
- `url`: download URL
- `checksum`: MD5 for integrity check
- `sizeInBytes`

### Step 5 - Download file

```
GET {url}  (no auth header needed - URL is pre-signed)
```

Response is gzip-compressed TSV. Decompress with `gzip.open()`.

### Dashboard-relevant report IDs (request 77203237-...)

156 reports total available. Pipeline uses only 5. IDs are stable per request_id (confirmed 2026-06-26):

| Report Name | Report ID | Category |
|---|---|---|
| App Store Installation and Deletion Standard | `r6-77203237-b1c3-40ed-bccf-ce4345c7d5ab` | APP_USAGE |
| App Sessions Standard | `r8-77203237-b1c3-40ed-bccf-ce4345c7d5ab` | APP_USAGE |
| App Downloads Standard | `r3-77203237-b1c3-40ed-bccf-ce4345c7d5ab` | COMMERCE |
| App Store Discovery and Engagement Standard | `r14-77203237-b1c3-40ed-bccf-ce4345c7d5ab` | APP_STORE_ENGAGEMENT |
| App Install Performance | `r5-77203237-b1c3-40ed-bccf-ce4345c7d5ab` | PERFORMANCE |

Remaining 151 reports = `FRAMEWORK_USAGE` (ARKit, Bluetooth, Metal, Widget usage, etc.) — not needed for dashboard, ignored by pipeline.

---

## Customer Reviews API (synchronous, no vendor number)

- **Endpoint:** `GET /v1/apps/1350501409/customerReviews`
- **Method:** GET, paginated via cursor
- **Verified live (2026-06-26):** 200+ reviews returned, data current

| Parameter | Value |
|---|---|
| `limit` | max 200 per page |
| `sort` | `-createdDate` (newest first) |
| `filter[rating]` | optional, e.g. `1,2` for low-star filter |

### Response fields

| Field | Type | Description |
|---|---|---|
| `id` | STRING | Unique review ID |
| `attributes.rating` | INTEGER (1-5) | Star rating |
| `attributes.title` | STRING | Review title |
| `attributes.body` | STRING | Review text |
| `attributes.reviewerNickname` | STRING | Reviewer display name |
| `attributes.createdDate` | ISO8601 | Review creation date |
| `attributes.territory` | STRING | 3-letter country code (e.g. `IDN`) |

Pagination: follow `links.next` until absent.

---

## Sales Reports API (requires vendor number)

- **Endpoint:** `GET /v1/salesReports`
- **Auth:** same JWT
- **Response:** gzip TSV (`Accept: application/a-gzip`)
- **Status (2026-06-26):** HTTP 400 - `APPSTORE_VENDOR_NUMBER` not yet obtained

**Required parameters:**

| Parameter | Value |
|---|---|
| `filter[reportType]` | `SALES` or `SUBSCRIPTION` |
| `filter[reportSubType]` | `SUMMARY` |
| `filter[frequency]` | `DAILY` or `WEEKLY` |
| `filter[vendorNumber]` | vendor number (find: App Store Connect > Agreements, Tax, and Banking) |
| `filter[reportDate]` | `YYYY-MM-DD` for daily, `YYYY-MM-DD` (Sunday) for weekly |

---

## Finance Reports API (requires vendor number)

- **Endpoint:** `GET /v1/financeReports`
- **Response:** gzip TSV
- **Status (2026-06-26):** HTTP 400 - vendor number not yet obtained

**Required parameters:**

| Parameter | Value |
|---|---|
| `filter[reportType]` | `FINANCE_DETAIL` |
| `filter[vendorNumber]` | vendor number |
| `filter[regionCode]` | `ID` for Indonesia (or omit for all regions) |
| `filter[reportDate]` | `YYYY-MM` (monthly) |

---

## Metadata Columns (all tables, planned)

Same 7-column standard as other sources:

| Column | Type | Description |
|---|---|---|
| `_ingested_at` | TIMESTAMP | When the row was loaded into BigQuery |
| `_source` | STRING | Always `app_store` |
| `_run_id` | STRING | UUID identifying this extract run |
| `_extract_from` | DATE | date_from passed to the extract job |
| `_extract_to` | DATE | date_to passed to the extract job |
| `_app_id` | STRING | App Store app ID (`1350501409`) |
| `_platform` | STRING | Always `ios` |

---

## GCP Infra (NOT YET PROVISIONED - 2026-06-26)

Provision after analytics instances confirmed and vendor number obtained. Commands in `docs/runbook.md §17`.

| Resource | Status |
|---|---|
| SA `sa-extract-app-store` | PENDING |
| IAM: bigquery.dataEditor + jobUser | PENDING |
| Secret `appstore-connect-key` (.p8 content) | PENDING |
| IAM: secretmanager.secretAccessor | PENDING |
| BQ datasets: appstore_raw, appstore_staging, appstore_mart | PENDING |
| Cloud Run Job: extract-app-store | PENDING |

---

## Ingestion Code Status

Reviews ingestion: **IMPLEMENTED** at `ingestion/src/tring_ingest/sources/app_store/` (2026-06-26).

- `client.py` — ES256 JWT auth with token caching (auto-refresh 60s before expiry)
- `extract.py` — incremental reviews pull: fetches reviews with `createdDate >= date_from`, stops pagination when date threshold crossed (Apple returns newest-first)
- `cli.py` — `app_store` source wired, runs via `python -m tring_ingest --source app_store --from YYYY-MM-DD --to YYYY-MM-DD`
- `config.py` — `APPSTORE_SECRET_NAME`, `APPSTORE_APP_ID`, `BQ_DATASET_RAW_APPSTORE` added

**Reviews backfill:** run with `--from 2018-01-01` to get all 11,488 reviews (Tring! launched Mar 2018). Daily runs use `--from yesterday`.

**Analytics (installs/sessions/downloads/engagement) ingestion: NOT YET IMPLEMENTED.** Still needs async 4-step flow:
1. On first run: POST request (accessType=ONGOING), store request_id
2. On each run: GET instances for each target report, filter by processingDate not yet ingested
3. GET segments for each new instance
4. Download + decompress gzip TSV
5. Load to BQ raw table

Sales/Finance: synchronous GET, needs vendor number first.

---

## Known Behaviors and Limitations

- **Analytics API is async:** POST request → Apple generates files → GET instances. Instances = 0 for 24-48h after first request. After that, new daily instances appear automatically for ONGOING requests.
- **Reviews incremental, not full:** extractor pulls reviews with `createdDate >= date_from`. Staging deduplicates by `review_id`. Safe to re-run.
- **Reviews all-time available:** Apple returns all reviews since app launch (Mar 2018). 11,488 total as of 2026-06-26. Run with `--from 2018-01-01` for full backfill.
- **Vendor number required for sales/finance:** Find in App Store Connect > Agreements, Tax, and Banking > Vendor Number.
- **JWT auto-refresh in client.py:** token cached, refreshed 60s before 20-min expiry. No manual intervention needed.
- **Analytics report files are large:** Each gzip TSV can be several MB. Use chunked BQ loading (same pattern as AppsFlyer `in_app_events`).
- **ONE_TIME_SNAPSHOT** untuk backfill analytics historis (2024-2025): POST sekali → Apple generate semua data historis → download. Batas 1x/bulan. Instance tersedia 35 hari. Kuota Juni sudah terpakai — lakukan Juli 2026.
- **ONGOING vs ONE_TIME_SNAPSHOT:** pipeline daily pakai ONGOING (sekali POST, reuse selamanya). Backfill analytics pakai ONE_TIME_SNAPSHOT.
