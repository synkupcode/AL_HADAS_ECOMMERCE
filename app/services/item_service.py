import json
from typing import Any, Dict, Optional, List
from datetime import datetime, timezone

from app.integrations.erp_client import erp_request
from app.services.ecommerce.visibility_engine import apply_visibility_rules
from app.services.ecommerce.pricing_engine import apply_pricing_rules

DEFAULT_PAGE_SIZE = 100

ERP_BASE_URL = ""  # Keep blank, use normalize_image from utils if needed


def normalize_image(image_path: Optional[str]) -> str:
    """
    Converts relative ERP image paths into full URLs.
    Leaves full URLs unchanged.
    """
    if not image_path:
        return ""
    if image_path.startswith("http"):
        return image_path
    from app.core.config import settings
    if settings.ERP_BASE_URL:
        return f"{settings.ERP_BASE_URL}{image_path}"
    return image_path


def get_products(
    category: Optional[str] = None,
    subcategory: Optional[str] = None,
    search: Optional[str] = None,
    order_by: Optional[str] = None,
    page: int = 1,
    page_size: int = DEFAULT_PAGE_SIZE,
) -> Dict[str, Any]:

    if page < 1:
        page = 1
    if page_size < 1:
        page_size = DEFAULT_PAGE_SIZE

    # -------------------------
    # FILTERS
    # -------------------------
    filters: List[Any] = [
        ["disabled", "=", 0],
        ["custom_enable_item", "=", 1],  # Only items enabled for ecommerce
    ]
    if category:
        filters.append(["item_group", "=", category])
    if subcategory:
        filters.append(["custom_subcategory", "=", subcategory])

    # -------------------------
    # FIELDS
    # -------------------------
    fields = [
        "item_code",
        "item_name",
        "description",
        "image",
        "item_group",
        "custom_subcategory",
        "custom_pricing_rule",
        "custom_ecommerce_price",
        "custom_mrp_price",
        "custom_enable_promotion",
        "custom_promotion_start",
        "custom_promotion_end",
        "custom_promotion_base_price",
        "custom_promotion_type",
        "custom_promotion_price_manual",
        "custom_promotional_price",
        "custom_promotion_discount_",
        "custom_standard_selling_price",
        "custom_show_price",
        "custom_show_image",
        "custom_show_stock",
        "show_strike_price",
    ]

    # -----------------------------
    # COUNT FOR PAGINATION
    # -----------------------------
    count_params = {
        "filters": json.dumps(filters),
        "fields": '["name"]',
        "limit_page_length": 0,
    }
    count_res = erp_request("GET", "/api/resource/Item", params=count_params)
    total_items = len(count_res.get("data", []))
    total_pages = (total_items + page_size - 1) // page_size if page_size else 1

    # -----------------------------
    # DATA REQUEST
    # -----------------------------
    start = (page - 1) * page_size
    params = {
        "filters": json.dumps(filters),
        "fields": json.dumps(fields),
        "limit_start": start,
        "limit_page_length": page_size,
        "order_by": (
            "standard_rate asc" if order_by == "price_asc" else
            "standard_rate desc" if order_by == "price_desc" else
            "modified desc"
        ),
    }

    response = erp_request("GET", "/api/resource/Item", params=params)
    items = response.get("data", []) or []

    # -----------------------------
    # SEARCH FILTER (POST PROCESS)
    # -----------------------------
    if search:
        search_lower = search.lower()
        items = [
            item for item in items
            if search_lower in (item.get("item_name") or "").lower()
            or search_lower in (item.get("item_code") or "").lower()
        ]

    # -----------------------------
    # APPLY PRICING & VISIBILITY
    # -----------------------------
    formatted_items = []

    for item in items:
        # Apply ecommerce pricing rules
        item = apply_pricing_rules(item)
        # Apply visibility rules
        item = apply_visibility_rules(item)
        # Normalize image URL
        item["image"] = normalize_image(item.get("image"))

        formatted_items.append({
            "item_code": item.get("item_code"),
            "item_name": item.get("item_name"),
            "description": item.get("description"),
            "price": item.get("price"),
            "original_price": item.get("original_price"),
            "discount_percentage": item.get("discount_percentage"),
            "is_on_sale": item.get("is_on_sale", False),
            "image": item.get("image"),
            "stock_status": item.get("stock_status"),
            "category": item.get("item_group"),
            "subcategory": item.get("custom_subcategory"),
            "is_price_visible": item.get("is_price_visible"),
            "is_image_visible": item.get("is_image_visible"),
        })

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
