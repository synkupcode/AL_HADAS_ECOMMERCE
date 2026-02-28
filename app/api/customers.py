from fastapi import APIRouter, HTTPException, Header
from typing import Optional

from app.core.config import settings
from app.services.customer_service import _find_customer_by_phone

router = APIRouter(prefix="", tags=["customers"])


# -----------------------------
# Frontend Token Protection
# -----------------------------
def _require_frontend_token(x_frontend_token: Optional[str]) -> None:
    if not settings.FRONTEND_SECRET_TOKEN:
        return

    if x_frontend_token != settings.FRONTEND_SECRET_TOKEN:
        raise HTTPException(status_code=401, detail="Unauthorized")


# -----------------------------
# Check If Customer Exists
# -----------------------------
@router.get("/customer/exists")
def customer_exists(
    phone: str,
    x_frontend_token: Optional[str] = Header(default=None, alias="X-Frontend-Token"),
):
    _require_frontend_token(x_frontend_token)

    if not phone:
        raise HTTPException(status_code=400, detail="Phone is required")

    try:
        existing = _find_customer_by_phone(phone)

        return {
            "status": "success",
            "exists": bool(existing),
            "customer_id": existing,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
