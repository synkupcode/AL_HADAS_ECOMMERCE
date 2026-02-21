from fastapi import APIRouter, HTTPException, Header
from typing import Optional

from app.core.config import settings
from app.services.customer_service import get_customer_id_by_phone

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
        cid = get_customer_id_by_phone(phone)
        return {"status": "success", "exists": bool(cid), "customer_id": cid}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))