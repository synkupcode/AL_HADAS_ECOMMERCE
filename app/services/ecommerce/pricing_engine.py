from datetime import datetime
from typing import Dict, Any


def _is_promotion_active(item: Dict[str, Any]) -> bool:
    if not item.get("custom_enable_promotion"):
        return False

    start = item.get("custom_promotion_start")
    end = item.get("custom_promotion_end")

    if not start or not end:
        return False

    today = datetime.utcnow().date()

    try:
        start_date = datetime.strptime(start, "%Y-%m-%d").date()
        end_date = datetime.strptime(end, "%Y-%m-%d").date()
    except Exception:
        return False

    return start_date <= today <= end_date


def apply_pricing_rules(item: Dict[str, Any]) -> Dict[str, Any]:
    """
    Applies ecommerce pricing engine logic.
    """

    pricing_mode = item.get("custom_pricing_rule")

    # -------------------------
    # FIXED PRICE MODE
    # -------------------------
    if pricing_mode == "Fixed Price":
        item["price"] = item.get("custom_ecommerce_price") or 0
        item["is_on_sale"] = False
        return item

    # -------------------------
    # MRP MODE
    # -------------------------
    if pricing_mode == "MRP":
        item["price"] = item.get("custom_mrp_price") or 0
        item["is_on_sale"] = False
        return item

    # -------------------------
    # PROMOTIONAL MODE
    # -------------------------
    if pricing_mode == "Promotional Rate" and _is_promotion_active(item):

        base_price = (
            item.get("custom_ecommerce_price")
            if item.get("custom_promotion_base_price") == "E-Commerce"
            else item.get("custom_standard_selling_price")
        )

        promo_type = item.get("custom_promotion_type")

        if promo_type == "Manual Pricing":
            promo_price = item.get("custom_promotion_price_manual") or 0
        else:
            promo_price = item.get("custom_promotional_price") or 0

        item["price"] = promo_price
        item["is_on_sale"] = True

        # Strike logic
        if item.get("show_strike_price"):
            item["original_price"] = base_price
            item["discount_percentage"] = item.get("custom_promotion_discount_")

        return item

    # Fallback
    item["price"] = item.get("custom_ecommerce_price") or 0
    item["is_on_sale"] = False

    return item
