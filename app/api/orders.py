from fastapi import APIRouter, HTTPException, Header
from typing import Optional

from app.core.config import settings
from app.models.order_models import PlaceOrderIn
from app.services.order_service import create_ecommerce_rfq
from app.services.order_tracking import (
    list_orders_by_phone,
    get_order_detail,
)

router = APIRouter(prefix="", tags=["orders"])


def _require_frontend_token(x_frontend_token: Optional[str]) -> None:
    """
    Simple frontend token validation (MVP protection).
    """
    if not settings.FRONTEND_SECRET_TOKEN:
        return

    if x_frontend_token != settings.FRONTEND_SECRET_TOKEN:
        raise HTTPException(status_code=401, detail="Unauthorized")


@router.post("/checkout/place-order")
def place_order(
    payload: PlaceOrderIn,
    x_frontend_token: Optional[str] = Header(
        default=None,
        alias="X-Frontend-Token",
    ),
):
    _require_frontend_token(x_frontend_token)

    try:
        # Convert Pydantic model to dict
        return create_ecommerce_rfq(payload.model_dump())

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/orders")
def my_orders(
    phone_number: str,
    limit: int = 50,
    x_frontend_token: Optional[str] = Header(
        default=None,
        alias="X-Frontend-Token",
    ),
):
    _require_frontend_token(x_frontend_token)

    # Hard cap limit to avoid abuse
    if limit > 100:
        limit = 100

    try:
        return list_orders_by_phone(
            phone_number=phone_number,
            limit=limit,
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/orders/{rfq_id}")
def order_detail(
    rfq_id: str,
    x_frontend_token: Optional[str] = Header(
        default=None,
        alias="X-Frontend-Token",
    ),
):
    _require_frontend_token(x_frontend_token)

    try:
        return get_order_detail(rfq_id)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
