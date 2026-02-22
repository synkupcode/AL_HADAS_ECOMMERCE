# app/services/item_service.py

import json
from typing import Any, Dict, Optional, List
from datetime import datetime, timezone

from app.integrations.erp_client import erp_request


DEFAULT_PAGE_SIZE = 100


def get_products(
    category: Optional[str] = None,
    subcategory: Optional[str] = None,
    search: Optional[str] = None,
    page: int = 1,
    page_size: int = DEFAULT_PAGE_SIZE,
) -> Dict[str, Any]:
    """
    Fetch products from ERPNext with:
    - Category filter
    - Subcategory filter
    - Search (item_name OR item_code)
    - Pagination
    - Clean transformed response
    """

    # Validate pagination
    if page < 1:
        page = 1

    if page_size < 1:
        page_size = DEFAULT_PAGE_SIZE

    # Base filters
    filters: List[Any] = [
        ["disabled", "=", 0],
    ]

    # Category filter (ERP field: item_group)
    if category:
        filters.append(["item_group", "=", category])

    # Subcategory filter (custom field)
    if subcategory:
        filters.append(["custom_subcategory", "=", subcategory])

    # Fields we request from ERP
    fields = [
        "item_code",
        "item_name",
        "custom_subcategory",
        "image",
        "description",
        "standard_rate",
        "item_group",
    ]

    # Pagination
    start = (page - 1) * page_size

    params = {
        "filters": json.dumps(filters),
        "fields": json.dumps(fields),
        "limit_start": start,
        "limit_page_length": page_size,
        "order_by": "modified desc",
    }

    # Fetch from ERP
    response = erp_request(
        "GET",
        "/api/resource/Item",
        params=params,
    )

    items = response.get("data", []) or []

    # ----------------------------
    # SEARCH FILTER (PYTHON LEVEL)
    # ----------------------------
    if search:
        search_lower = search.lower()
        items = [
            item for item in items
            if search_lower in (item.get("item_name") or "").lower()
            or search_lower in (item.get("item_code") or "").lower()
        ]

    # Transform ERP → Clean API structure
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
