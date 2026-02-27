from fastapi import APIRouter, HTTPException, Header
from typing import Optional
import json

from app.core.config import settings
from app.integrations.erp_client import erp_request

router = APIRouter(prefix="", tags=["customers"])


def _require_frontend_token(x_frontend_token: Optional[str]) -> None:
    """
    Validate frontend secret token if configured.
    """
    if not settings.FRONTEND_SECRET_TOKEN:
        return

    if x_frontend_token != settings.FRONTEND_SECRET_TOKEN:
        raise HTTPException(status_code=401, detail="Unauthorized")


@router.get("/customer/exists")
def customer_exists(
    phone: str,
    x_frontend_token: Optional[str] = Header(None),
):
    """
    Check if a customer exists by phone number.
    Searches directly in Customer doctype using custom_phone_number.
    """

    _require_frontend_token(x_frontend_token)

    if not phone:
        raise HTTPException(status_code=400, detail="Phone is required")

    try:
        filters = [["custom_phone_number", "=", phone]]

        res = erp_request(
            "GET",
            "/api/resource/Customer",
            params={
                "filters": json.dumps(filters),
                "fields": json.dumps(["name"]),
                "limit_page_length": 1,
            },
        )

        data = res.get("data") or []

        if not data:
            return {
                "status": "success",
                "exists": False,
                "customer_id": None,
            }

        return {
            "status": "success",
            "exists": True,
            "customer_id": data[0]["name"],
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
