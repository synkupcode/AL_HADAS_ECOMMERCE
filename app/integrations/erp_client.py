
from __future__ import annotations
import requests
from typing import Any, Optional
import time
from requests.exceptions import RequestException
from app.core.config import settings

class ERPError(Exception):
    """Structured exception for ERP request failures."""
    def __init__(self, message: str, status_code: int = None):
        super().__init__(message)
        self.status_code = status_code


def erp_request(
    method: str,
    path: str,
    params: Optional[dict[str, Any]] = None,
    json: Optional[dict[str, Any]] = None,
    retries: int = 3,
    backoff_factor: float = 1.0,
) -> dict[str, Any]:
    """
    Makes a request to ERP API with retries and structured errors.
    """
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

    attempt = 0
    while attempt < retries:
        try:
            response = requests.request(
                method=method.upper(),
                url=url,
                headers=headers,
                params=params,
                json=json,
                timeout=30,
            )
        except RequestException as exc:
            attempt += 1
            if attempt >= retries:
                raise ERPError(f"ERP connection failed after {retries} attempts: {exc}") from exc
            time.sleep(backoff_factor * attempt)
            continue

        # Handle HTTP errors
        if response.status_code >= 400:
            raise ERPError(f"ERP error {response.status_code}: {response.text}", status_code=response.status_code)

        try:
            return response.json()
        except ValueError:
            raise ERPError(f"Invalid ERP JSON response: {response.text}")
