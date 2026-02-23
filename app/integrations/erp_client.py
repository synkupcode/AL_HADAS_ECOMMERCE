from __future__ import annotations
import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
from typing import Any, Optional
from app.core.config import settings

class ERPError(Exception):
    pass

session = requests.Session()
retries = Retry(total=3, backoff_factor=0.5, status_forcelist=[500,502,503,504])
session.mount("https://", HTTPAdapter(max_retries=retries))

def erp_request(method: str, path: str, params: Optional[dict[str, Any]] = None, json: Optional[dict[str, Any]] = None) -> dict[str, Any]:
    if not settings.ERP_BASE_URL:
        raise ERPError("ERP_BASE_URL not configured.")
    if not settings.ERP_API_KEY or not settings.ERP_API_SECRET:
        raise ERPError("ERP API credentials not configured.")

    url = f"{settings.ERP_BASE_URL}{path}"
    headers = {
        "Authorization": f"token {settings.ERP_API_KEY}:{settings.ERP_API_SECRET}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    try:
        response = session.request(
            method=method.upper(),
            url=url,
            headers=headers,
            params=params,
            json=json,
            timeout=30,
        )
    except requests.RequestException as exc:
        raise ERPError(f"ERP connection failed: {exc}") from exc

    if response.status_code >= 400:
        raise ERPError(f"ERP error {response.status_code}: {response.text}")

    try:
        return response.json()
    except ValueError:
        raise ERPError(f"Invalid ERP response: {response.text}")
