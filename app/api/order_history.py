from fastapi import APIRouter, Depends, Query

from app.auth.dependencies import get_current_user
from app.services.order_history_service import get_user_orders

router = APIRouter(prefix="/orders", tags=["Order History"])


@router.get("/my")
def my_orders(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user=Depends(get_current_user),
):
    return get_user_orders(
        email=current_user["sub"],
        limit=limit,
        offset=offset,
    )
