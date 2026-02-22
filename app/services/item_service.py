import json
import os
from typing import Any, Dict, Optional, List
from datetime import datetime, timezone

from app.integrations.erp_client import erp_request


DEFAULT_PAGE_SIZE = 100

# -------------------------------------------------
# ERP BASE URL (set this in Render environment)
# Example:
# ERP_BASE_URL = https://aerictec.frappe.cloud
# -------------------------------------------------
ERP_BASE_URL = os.getenv("ERP_BASE_URL", "").rstrip("/")


def normalize_image(image_path: Optional[str]) -> str:
    """
    Converts relative ERP image paths into full URLs.
    Leaves full URLs unchanged.
    """
    if not image_path:
        return ""

    # If already a full URL, return as-is
    if image_path.startswith("http"):
        return image_path

    # If ERP base URL is configured, prepend it
    if ERP_BASE_URL:
        return f"{ERP_BASE_URL}{image_path}"

    # Fallback (in case env not set)
    return image_path


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
    erp_order = "modified desc"

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
    # TOTAL COUNT
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
    # SEARCH FILTER (POST PROCESS)
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
            "image": normalize_image(item.get("image")),
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
