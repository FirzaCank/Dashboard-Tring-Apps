"""HTTP session with retry and exponential backoff."""

import requests
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from tring_ingest.common.logging import get_logger

logger = get_logger(__name__)

_RETRY_STATUS_CODES = {429, 500, 502, 503, 504}


class RetryableHTTPError(Exception):
    pass


def _is_retryable(response: requests.Response) -> bool:
    return response.status_code in _RETRY_STATUS_CODES


def build_session(bearer_token: str) -> requests.Session:
    session = requests.Session()
    session.headers.update({"Authorization": f"Bearer {bearer_token}"})
    return session


@retry(
    retry=retry_if_exception_type(RetryableHTTPError),
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=2, min=4, max=30),
    reraise=True,
)
def get_with_retry(session: requests.Session, url: str, params: dict) -> requests.Response:
    logger.info("HTTP GET", extra={"url": url, "params": params})
    response = session.get(url, params=params, timeout=120)

    if _is_retryable(response):
        logger.warning(
            "Retryable HTTP error",
            extra={"status_code": response.status_code, "url": url},
        )
        raise RetryableHTTPError(f"HTTP {response.status_code} from {url}")

    if not response.ok:
        logger.error(
            "Non-retryable HTTP error",
            extra={"status_code": response.status_code, "url": url, "body": response.text[:500]},
        )
        response.raise_for_status()

    return response
