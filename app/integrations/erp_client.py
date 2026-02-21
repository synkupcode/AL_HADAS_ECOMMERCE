from __future__ import annotations

import requests
from typing import Any, Optional

from app.core.config import settings


class ERPError(Exception):
    pass


def erp_request(
    method: str,
    path: str,
    params: Optional[dict[str, Any]] = None,
    json: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    """
    Generic ERPNext request helper.
    Uses standard Frappe token authentication.
    """

    # Validate configuration
    if not settings.ERP_BASE_URL:
        raise ERPError("ERP_BASE_URL is not configured.")

    if not settings.ERP_API_KEY or not settings.ERP_API_SECRET:
        raise ERPError("ERP API credentials are not configured.")

    # Build full URL
    url = f"{settings.ERP_BASE_URL}{path}"

    # Standard Frappe API Token format
    headers = {
        "Authorization": f"token {settings.ERP_API_KEY}:{settings.ERP_API_SECRET}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    try:
        response = requests.request(
            method=method.upper(),
            url=url,
            headers=headers,
            params=params,
            json=json,
            timeout=30,
        )
    except requests.RequestException as exc:
        raise ERPError(f"ERP request failed: {exc}") from exc

    # Handle ERP errors
    if response.status_code >= 400:
        raise ERPError(
            f"ERP error {response.status_code}: {response.text}"
        )

    # Return JSON safely
    try:
        return response.json()
    except ValueError:
        raise ERPError(f"Invalid JSON response from ERP: {response.text}")