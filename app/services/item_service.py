import json
import os
from typing import Any, Dict, Optional, List
from datetime import datetime, timezone

from fastapi import HTTPException

from app.core.site_control import SiteControl
from app.integrations.erp_client import erp_request
from app.services.ecommerce.ecommerce_engine import EcommerceEngine


DEFAULT_PAGE_SIZE = 100
ERP_BASE_URL = os.getenv("ERP_BASE_URL", "").rstrip("/")


def normalize_image(image_path: Optional[str]) -> str:
    if not image_path:
        return ""

    if image_path.startswith("http"):
        return image_path

    if ERP_BASE_URL:
        return f"{ERP_BASE_URL}{image_path}"

    return image_path


def get_products(
    category: Optional[str] = None,
    subcategory: Optional[str] = None,
    search: Optional[str] = None,
    order_by: Optional[str] = None,
    page: int = 1,
    page_size: int = DEFAULT_PAGE_SIZE,
) -> Dict[str, Any]:

    # -------------------------------------------------
    # 🔐 MASTER INTEGRATION SWITCH
    # -------------------------------------------------
    if not SiteControl.is_website_integration_enabled():
        raise HTTPException(
            status_code=503,
            detail="E-commerce integration is currently disabled."
        )

    # -------------------------------------------------
    # 🔐 GLOBAL CATALOG SWITCH
    # -------------------------------------------------
    if not SiteControl.is_item_sync_enabled():
        return {
            "status": "catalog_disabled",
            "items": [],
            "pagination": {
                "page": 1,
                "page_size": 0,
                "total_items": 0,
                "total_pages": 0,
            },
            "last_sync": None,
        }

    if page < 1:
        page = 1

    if page_size < 1:
        page_size = DEFAULT_PAGE_SIZE

    # -------------------------------------------------
    # FILTERS
    # -------------------------------------------------
    filters: List[Any] = [
        ["disabled", "=", 0],
        ["custom_enable_item", "=", 1],
    ]

    if category:
        filters.append(["item_group", "=", category])

    if subcategory:
        filters.append(["custom_subcategory", "=", subcategory])

    # -------------------------------------------------
    # FIELDS
    # -------------------------------------------------
    fields = [
        "item_code",
        "item_name",
        "custom_subcategory",
        "image",
        "description",
        "item_group",
        "custom_standard_selling_price",
        "custom_ecommerce_price",
        "custom_mrp_price",
        "custom_fixed_price",
        "custom_mrp_rate",
        "custom_enable_promotion",
        "custom_promotion_base_price",
        "custom_promotion_type",
        "custom_promotion_discount_",
        "custom_promotion_start",
        "custom_promotion_end",
        "custom_promotion_price_manual",
        "custom_promotional_price",
        "custom_promotional_rate",
        "custom_show_strike_price",
        "custom_show_price",
        "custom_show_image",
        "custom_show_stock",
    ]

    start = (page - 1) * page_size

    params = {
        "filters": json.dumps(filters),
        "fields": json.dumps(fields),
        "limit_start": start,
        "limit_page_length": page_size,
        "order_by": "modified desc",
    }

    # -------------------------------------------------
    # TOTAL COUNT
    # -------------------------------------------------
    count_response = erp_request(
        "GET",
        "/api/resource/Item",
        params={
            "filters": json.dumps(filters),
            "fields": json.dumps(["name"]),
            "limit_page_length": 0,
        },
    )

    total_items = len(count_response.get("data", []) or [])
    total_pages = (total_items + page_size - 1) // page_size if page_size > 0 else 1

    # -------------------------------------------------
    # MAIN DATA REQUEST
    # -------------------------------------------------
    response = erp_request(
        "GET",
        "/api/resource/Item",
        params=params,
    )

    items = response.get("data", []) or []

    if search:
        search_lower = search.lower()
        items = [
            item for item in items
            if search_lower in (item.get("item_name") or "").lower()
            or search_lower in (item.get("item_code") or "").lower()
        ]

    # -------------------------------------------------
    # TRANSFORM
    # -------------------------------------------------
    formatted_items = []

    for item in items:

        ecommerce_data = EcommerceEngine.transform_item(item)

        # 🔐 ONLY CONTROL DISPLAY — DO NOT OVERRIDE ENGINE VALUES
        is_price_visible_global = SiteControl.is_price_visibility_enabled()

        formatted_items.append({
            "item_code": item.get("item_code") or "",
            "item_name": item.get("item_name") or "",
            "description": item.get("description") or "",
            "price": ecommerce_data["price"] if is_price_visible_global else None,
            "original_price": ecommerce_data["original_price"],
            "discount_percentage": ecommerce_data["discount_percentage"],
            "is_on_sale": ecommerce_data["is_on_sale"],
            "image": normalize_image(
                ecommerce_data["image"]
            ),
            "category": item.get("item_group") or "Uncategorized",
            "subcategory": item.get("custom_subcategory") or "Other",
            "stock_status": ecommerce_data["stock_status"],
            "is_price_visible": ecommerce_data["is_price_visible"],
            "is_image_visible": ecommerce_data["is_image_visible"],
        })

    # -------------------------------------------------
    # FINAL RESPONSE
    # -------------------------------------------------
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
