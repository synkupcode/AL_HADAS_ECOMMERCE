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
    order_by: Optional[str] = None,
    page: int = 1,
    page_size: int = DEFAULT_PAGE_SIZE,
) -> Dict[str, Any]:

    # --------------------
    # VALIDATION
    # --------------------
    if page < 1:
        page = 1

    if page_size < 1:
        page_size = DEFAULT_PAGE_SIZE

    # --------------------
    # FILTERS
    # --------------------
    filters: List[Any] = [
        ["disabled", "=", 0],
    ]

    if category:
        filters.append(["item_group", "=", category])

    if subcategory:
        filters.append(["custom_subcategory", "=", subcategory])

    # --------------------
    # FIELDS
    # --------------------
    fields = [
        "item_code",
        "item_name",
        "custom_subcategory",
        "image",
        "description",
        "standard_rate",
        "item_group",
    ]

    # --------------------
    # SORTING
    # --------------------
    erp_order = "modified desc"  # default

    if order_by == "price_asc":
        erp_order = "standard_rate asc"

    elif order_by == "price_desc":
        erp_order = "standard_rate desc"

    elif order_by == "newest":
        erp_order = "modified desc"

    # --------------------
    # PAGINATION
    # --------------------
    start = (page - 1) * page_size

    params = {
        "filters": json.dumps(filters),
        "fields": json.dumps(fields),
        "limit_start": start,
        "limit_page_length": page_size,
        "order_by": erp_order,
    }

    # --------------------
    # TOTAL COUNT (FOR PAGINATION)
    # --------------------
    count_params = {
        "filters": json.dumps(filters),
        "limit_page_length": 0,
        "fields": json.dumps(["name"]),
    }

    count_response = erp_request(
        "GET",
        "/api/resource/Item",
        params=count_params,
    )

    total_items = len(count_response.get("data", []) or [])

    total_pages = (
        (total_items + page_size - 1) // page_size
        if page_size > 0
        else 1
    )

    # --------------------
    # MAIN DATA REQUEST
    # --------------------
    response = erp_request(
        "GET",
        "/api/resource/Item",
        params=params,
    )

    items = response.get("data", []) or []

    # --------------------
    # PYTHON SEARCH (SAFE)
    # --------------------
    if search:
        search_lower = search.lower()
        items = [
            item for item in items
            if search_lower in (item.get("item_name") or "").lower()
            or search_lower in (item.get("item_code") or "").lower()
        ]

    # --------------------
    # FORMAT RESPONSE
    # --------------------
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
            "total_items": total_items,
            "total_pages": total_pages,
        },
        "last_sync": datetime.now(timezone.utc).isoformat(),
    }
