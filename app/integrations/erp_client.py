from __future__ import annotations

import logging
from typing import Any, Optional

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from app.core.config import settings


logger = logging.getLogger(__name__)


class ERPError(Exception):
    pass


# -----------------------------
# Session with Retry (Production Ready)
# -----------------------------
_session = requests.Session()

retry_strategy = Retry(
    total=3,
    backoff_factor=0.5,
    status_forcelist=[502, 503, 504],
    allowed_methods=["GET", "POST", "PUT", "DELETE"],
)

adapter = HTTPAdapter(max_retries=retry_strategy)
_session.mount("http://", adapter)
_session.mount("https://", adapter)


def erp_request(
    method: str,
    path: str,
    params: Optional[dict[str, Any]] = None,
    json: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:

    if not settings.ERP_BASE_URL:
        raise ERPError("ERP_BASE_URL not configured.")

    if not settings.ERP_API_KEY or not settings.ERP_API_SECRET:
        raise ERPError("ERP API credentials not configured.")

    url = f"{settings.ERP_BASE_URL}{path}"

    headers = {
        "Authorization": f"token {settings.ERP_API_KEY}:{settings.ERP_API_SECRET}",
        "Accept": "application/json",
    }

    try:
        response = _session.request(
            method=method.upper(),
            url=url,
            headers=headers,
            params=params,
            json=json,
            timeout=getattr(settings, "ERP_TIMEOUT", 30),
        )
    except requests.RequestException:
        logger.exception("ERP connection failed")
        raise ERPError("ERP connection failed")

    if response.status_code >= 400:
        logger.error(
            "ERP error | %s %s | %s | %s",
            method,
            path,
            response.status_code,
            response.text,
        )
        raise ERPError(f"ERP error {response.status_code} - {response.text}")

    try:
        return response.json()
    except ValueError:
        logger.error("Invalid ERP JSON response")
        raise ERPError("Invalid ERP response")
