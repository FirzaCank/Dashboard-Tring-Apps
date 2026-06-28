import time

import jwt
import requests

from tring_ingest.common.auth import get_secret
from tring_ingest.common.config import APPSTORE_SECRET_NAME
from tring_ingest.common.http import RetryableHTTPError
from tring_ingest.common.logging import get_logger

logger = get_logger(__name__)

_BASE = "https://api.appstoreconnect.apple.com"
_RETRY_STATUS_CODES = {429, 500, 502, 503, 504}
# Token valid 20 min; refresh 60s early
_TOKEN_TTL = 1140


class AppStoreClient:
    # creds format: "KEY_ID:ISSUER_ID" -- p8 key content from Secret Manager separately,
    # or pass all three as "KEY_ID:ISSUER_ID:P8_CONTENT" for tests.
    def __init__(self, creds: str | None = None):
        raw = creds or get_secret(APPSTORE_SECRET_NAME)
        parts = raw.split(":", 2)
        self._key_id = parts[0].strip()
        self._issuer_id = parts[1].strip()
        self._p8 = parts[2].strip() if len(parts) == 3 else get_secret(f"{APPSTORE_SECRET_NAME}-p8")
        self._token: str | None = None
        self._token_exp: float = 0
        self._session = requests.Session()

    def _get_token(self) -> str:
        now = time.time()
        if self._token and now < self._token_exp:
            return self._token
        iat = int(now)
        self._token = jwt.encode(
            {
                "iss": self._issuer_id,
                "iat": iat,
                "exp": iat + _TOKEN_TTL + 60,
                "aud": "appstoreconnect-v1",
            },
            self._p8,
            algorithm="ES256",
            headers={"kid": self._key_id},
        )
        self._token_exp = now + _TOKEN_TTL
        return self._token

    def _headers(self) -> dict:
        return {"Authorization": f"Bearer {self._get_token()}"}

    def get(self, url: str, params: dict | None = None) -> requests.Response:
        from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

        @retry(
            retry=retry_if_exception_type(RetryableHTTPError),
            stop=stop_after_attempt(3),
            wait=wait_exponential(multiplier=2, min=4, max=30),
            reraise=True,
        )
        def _get() -> requests.Response:
            resp = self._session.get(url, headers=self._headers(), params=params, timeout=120)
            if resp.status_code in _RETRY_STATUS_CODES:
                raise RetryableHTTPError(f"HTTP {resp.status_code} from {url}")
            if not resp.ok:
                logger.error(
                    "http error",
                    extra={"status": resp.status_code, "url": url, "body": resp.text[:500]},
                )
                resp.raise_for_status()
            return resp

        return _get()

    def get_unsigned(self, url: str) -> requests.Response:
        # signed s3 url for analytics segment download; no auth header, has its own signature
        from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

        @retry(
            retry=retry_if_exception_type(RetryableHTTPError),
            stop=stop_after_attempt(3),
            wait=wait_exponential(multiplier=2, min=4, max=30),
            reraise=True,
        )
        def _get() -> requests.Response:
            resp = self._session.get(url, timeout=120)
            if resp.status_code in _RETRY_STATUS_CODES:
                raise RetryableHTTPError(f"HTTP {resp.status_code} from segment url")
            if not resp.ok:
                resp.raise_for_status()
            return resp

        return _get()

    def post(self, url: str, payload: dict) -> requests.Response:
        from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

        @retry(
            retry=retry_if_exception_type(RetryableHTTPError),
            stop=stop_after_attempt(3),
            wait=wait_exponential(multiplier=2, min=4, max=30),
            reraise=True,
        )
        def _post() -> requests.Response:
            resp = self._session.post(
                url,
                headers={**self._headers(), "Content-Type": "application/json"},
                json=payload,
                timeout=120,
            )
            if resp.status_code in _RETRY_STATUS_CODES:
                raise RetryableHTTPError(f"HTTP {resp.status_code} from {url}")
            if not resp.ok:
                logger.error(
                    "http error",
                    extra={"status": resp.status_code, "url": url, "body": resp.text[:500]},
                )
                resp.raise_for_status()
            return resp

        return _post()
