"""AppsFlyer HTTP client: Bearer token auth, base URL, GET with retry."""

import requests

from tring_ingest.common.auth import get_secret
from tring_ingest.common.config import APPSFLYER_BASE_URL, APPSFLYER_SECRET_NAME
from tring_ingest.common.http import build_session, get_with_retry


class AppsFlierClient:
    def __init__(self, token: str | None = None):
        resolved_token = token or get_secret(APPSFLYER_SECRET_NAME)
        self._session: requests.Session = build_session(resolved_token)
        self._base_url = APPSFLYER_BASE_URL

    def get(self, path: str, params: dict) -> requests.Response:
        url = f"{self._base_url}{path}"
        return get_with_retry(self._session, url, params)
