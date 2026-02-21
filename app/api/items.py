from fastapi import APIRouter, HTTPException
from typing import Optional

from app.services.item_service import get_products

router = APIRouter(prefix="", tags=["items"])


@router.get("/products")
def products(
    subcategory: Optional[str] = None,
    page: int = 1,
    page_size: int = 100,
):
    """
    Fetch products with:
    - Business filters (inside service layer)
    - Optional subcategory filter
    - Pagination support
    """

    try:
        return get_products(
            subcategory=subcategory,
            page=page,
            page_size=page_size,
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e),
        )