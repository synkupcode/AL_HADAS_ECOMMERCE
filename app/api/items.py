from fastapi import APIRouter, HTTPException
from typing import Optional

from app.services.item_service import get_products

router = APIRouter(prefix="", tags=["items"])


@router.get("/products")
def products(
    category: Optional[str] = None,
    subcategory: Optional[str] = None,
    search: Optional[str] = None,
    order_by: Optional[str] = None,
    page: int = 1,
    page_size: int = 100,
):

    try:
        return get_products(
            category=category,
            subcategory=subcategory,
            search=search,
            order_by=order_by,
            page=page,
            page_size=page_size,
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
