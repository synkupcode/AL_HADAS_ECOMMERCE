# app/api/items.py

from fastapi import APIRouter, HTTPException
from typing import Optional

from app.services.item_service import get_products

router = APIRouter(prefix="", tags=["items"])


@router.get("/products")
def products(
    category: Optional[str] = None,
    subcategory: Optional[str] = None,
    search=search,
    page: int = 1,
    page_size: int = 100,
):
    """
    Fetch products with:
    - Category filter
    - Subcategory filter
    - Pagination
    """

    try:
        return get_products(
            category=category,
            subcategory=subcategory,
            search=search,
            page=page,
            page_size=page_size,
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e),
        )
