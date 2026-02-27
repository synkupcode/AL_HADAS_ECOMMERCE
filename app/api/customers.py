
from fastapi import APIRouter, HTTPException, Header
from typing import Optional
import json

from app.core.config import settings
from app.integrations.erp_client import erp_request

router = APIRouter(prefix="", tags=["customers"])


def _require_frontend_token(x_frontend_token: Optional[str]) -> None:
    if not settings.FRONTEND_SECRET_TOKEN:
        return
    if x_frontend_token != settings.FRONTEND_SECRET_TOKEN:
        raise HTTPException(status_code=401, detail="Unauthorized")


@router.get("/customer/exists")
def customer_exists(phone: str, x_frontend_token: Optional[str] = Header(None)):
    _require_frontend_token(x_frontend_token)

    try:
        if not phone:
            raise HTTPException(status_code=400, detail="Phone is required")

        # Search in Contact (correct structure)
        filters = [["phone_nos.phone", "=", phone]]

        res = erp_request(
            "GET",
            "/api/resource/Contact",
            params={
                "filters": json.dumps(filters),
                "fields": json.dumps(["name", "links"]),
            },
        )

        data = res.get("data") or []

        if not data:
            return {"status": "success", "exists": False, "customer_id": None}

        customer_id = None

        for contact in data:
            for link in contact.get("links", []):
                if link.get("link_doctype") == "Customer":
                    customer_id = link.get("link_name")
                    break

        return {
            "status": "success",
            "exists": True,
            "customer_id": customer_id,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
