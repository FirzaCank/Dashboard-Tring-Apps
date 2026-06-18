"""Orchestrates 4 endpoint pulls x 2 app IDs = 8 pulls per run. Lands verbatim into BQ raw."""

from tring_ingest.common.bq_loader import load_csv_to_raw
from tring_ingest.common.config import APPSFLYER_APP_IDS, BQ_DATASET_RAW_APPSFLYER, GCP_PROJECT
from tring_ingest.common.logging import get_logger
from tring_ingest.sources.appsflyer.client import AppsFlierClient
from tring_ingest.sources.appsflyer.endpoints import ENDPOINTS, build_params

logger = get_logger(__name__)


def run(date_from: str, date_to: str, token: str | None = None) -> None:
    """
    Pull all 4 AppsFlyer endpoints for both Android and iOS.
    Total: 8 HTTP calls per run. Each lands into appsflyer_raw verbatim.
    """
    client = AppsFlierClient(token=token)
    errors = []

    for app_id, platform in APPSFLYER_APP_IDS:
        for endpoint in ENDPOINTS:
            path = endpoint.path_template.format(app_id=app_id)
            params = build_params(date_from, date_to, endpoint.extra_params)

            logger.info(
                "Pulling endpoint",
                extra={
                    "endpoint": endpoint.name,
                    "app_id": app_id,
                    "platform": platform,
                    "from": date_from,
                    "to": date_to,
                },
            )

            try:
                response = client.get(path, params)
                csv_content = response.text

                rows_loaded = load_csv_to_raw(
                    csv_content=csv_content,
                    dataset_id=BQ_DATASET_RAW_APPSFLYER,
                    table_id=endpoint.bq_table,
                    source="appsflyer",
                    app_id=app_id,
                    platform=platform,
                    date_from=date_from,
                    date_to=date_to,
                    project_id=GCP_PROJECT,
                )

                logger.info(
                    "Pull complete",
                    extra={
                        "endpoint": endpoint.name,
                        "app_id": app_id,
                        "platform": platform,
                        "rows_loaded": rows_loaded,
                    },
                )

            except Exception as exc:
                logger.error(
                    "Pull failed",
                    extra={
                        "endpoint": endpoint.name,
                        "app_id": app_id,
                        "platform": platform,
                        "error": str(exc),
                    },
                )
                errors.append((endpoint.name, app_id, platform, exc))

    if errors:
        summary = [(e, a, p) for e, a, p, _ in errors]
        raise RuntimeError(f"Extract failed for {len(errors)} pull(s): {summary}")

    logger.info("All pulls complete", extra={"date_from": date_from, "date_to": date_to})
