# app/services/item_service.py
import json
from typing import Any, Dict, Optional, List
from datetime import datetime, timezone

from app.integrations.erp_client import erp_request


DEFAULT_PAGE_SIZE = 100


def get_products(
    subcategory: Optional[str] = None,
    page: int = 1,
    page_size: int = DEFAULT_PAGE_SIZE,
) -> Dict[str, Any]:
    """
    Fetch products from ERPNext with:
    - Business filters
    - Optional subcategory filter
    - Proper pagination
    - Clean transformed response
    """

    # Validate pagination inputs
    if page < 1:
        page = 1

    if page_size < 1:
        page_size = DEFAULT_PAGE_SIZE

    # Business Rules (disabled for now – future use)
# filters: List[Any] = [
#     ["disabled", "=", 0],
#     ["custom_enable_item", "=", 1],
# ]

# For now: only exclude disabled items
    filters: List[Any] = [
        ["disabled", "=", 0],
    ]

    # Optional subcategory filter
    if subcategory:
        filters.append(["custom_subcategory", "=", subcategory])

    # Fields we expose to frontend (controlled schema)
    fields = [
        "item_code",
        "item_name",
        "custom_subcategory",
        "image",
        "description",
        "standard_rate",
        "item_group",
    ]

    # Pagination calculation
    start = (page - 1) * page_size

    params = {
        "filters": json.dumps(filters),
        "fields": json.dumps(fields),
        "limit_start": start,
        "limit_page_length": page_size,
        "order_by": "modified desc",
    }

    # ERP Request
    response = erp_request(
        "GET",
        "/api/resource/Item",
        params=params,
    )

    items = response.get("data", []) or []

    # Transform ERP structure → Clean API structure
    formatted_items = [
        {
            "item_code": item.get("item_code") or "",
            "item_name": item.get("item_name") or "",
            "description": item.get("description") or "",
            "price": item.get("standard_rate") or 0,
            "image": item.get("image") or "",
            "category": item.get("item_group") or "Uncategorized",
            "subcategory": item.get("custom_subcategory") or "Other",
        }
        for item in items
    ]

    return {
        "status": "success",
        "items": formatted_items,
        "pagination": {
            "page": page,
            "page_size": page_size,
        },
        "last_sync": datetime.now(timezone.utc).isoformat(),
    }
