"""Fetch secrets from Secret Manager."""

from google.cloud import secretmanager

from tring_ingest.common.config import GCP_PROJECT
from tring_ingest.common.logging import get_logger

logger = get_logger(__name__)


def get_secret(secret_id: str, project_id: str = GCP_PROJECT) -> str:
    """Fetch the latest version of a Secret Manager secret."""
    client = secretmanager.SecretManagerServiceClient()
    name = f"projects/{project_id}/secrets/{secret_id}/versions/latest"
    response = client.access_secret_version(request={"name": name})
    payload = response.payload.data.decode("utf-8")
    logger.info("Secret fetched", extra={"secret_id": secret_id})
    return payload
