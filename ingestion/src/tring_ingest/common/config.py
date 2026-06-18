"""Environment config, app ID maps, dataset names."""

import os

# GCP
GCP_PROJECT = os.environ.get("GCP_PROJECT", "dashboard-tring-dev")
REGION = os.environ.get("REGION", "asia-southeast2")

# BigQuery datasets
BQ_DATASET_RAW_APPSFLYER = os.environ.get("BQ_DATASET_RAW", "appsflyer_raw")
BQ_DATASET_STAGING_APPSFLYER = "appsflyer_staging"
BQ_DATASET_MART_APPSFLYER = "appsflyer_mart"

# AppsFlyer
APPSFLYER_BASE_URL = "https://hq1.appsflyer.com"
APPSFLYER_SECRET_NAME = os.environ.get("APPSFLYER_SECRET_NAME", "appsflyer-api-token")

# App IDs: (app_id, platform) pairs
APPSFLYER_APP_IDS = [
    ("com.pegadaiandigital", "android"),
    ("id1350501409", "ios"),
]

# Timezone for all AppsFlyer API calls
APPSFLYER_TIMEZONE = "Asia/Jakarta"

# master-agg groupings (validated against Postman collection)
APPSFLYER_MASTER_AGG_GROUPINGS = "pid,c,install_time,geo"
APPSFLYER_MASTER_AGG_KPIS = "impressions,clicks,installs,cost"
APPSFLYER_MASTER_AGG_CURRENCY = "USD"
