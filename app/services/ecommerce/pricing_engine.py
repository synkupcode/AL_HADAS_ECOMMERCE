from typing import Dict, Any

def apply_pricing_rules(item: Dict[str, Any]) -> Dict[str, Any]:
    """
    Apply ecommerce pricing rules based on ecommerce tab.
    Supports:
    - Fixed Price
    - MRP
    - Promotional Price (Manual or Percentage)
    """

    # -------------------------
    # Base prices
    # -------------------------
    ecommerce_price = item.get("custom_ecommerce_price") or 0
    mrp_price = item.get("custom_mrp_price") or 0
    standard_price = item.get("custom_standard_selling_price") or 0

    price_rule = item.get("custom_pricing_rule", "fixed_price").lower()
    enable_promotion = bool(item.get("custom_enable_promotion", 0))
    promotion_type = item.get("custom_promotion_type", "").lower()
    promo_manual = item.get("custom_promotion_price_manual") or 0
    promo_percentage = float(item.get("custom_promotion_discount_") or 0)
    promo_price_auto = item.get("custom_promotional_price") or 0

    # -------------------------
    # Determine base price
    # -------------------------
    if price_rule == "fixed_price":
        base_price = ecommerce_price
    elif price_rule == "mrp":
        base_price = mrp_price
    elif price_rule == "promotion" and enable_promotion:
        # Promotion rules
        if promotion_type == "manual":
            base_price = promo_manual
        else:
            # Percentage discount
            base_price = promo_price_auto
    else:
        base_price = standard_price  # fallback

    # -------------------------
    # Original price for strike
    # -------------------------
    original_price = None
    discount_percentage = 0
    is_on_sale = False
    show_strike = bool(item.get("show_strike_price", 0))

    if enable_promotion and price_rule == "promotion":
        is_on_sale = True
        if promotion_type == "percentage":
            original_price = ecommerce_price if show_strike else None
            discount_percentage = promo_percentage
        elif promotion_type == "manual":
            original_price = ecommerce_price if show_strike else None
            discount_percentage = round((original_price - base_price) / original_price * 100, 2) if original_price else 0

    # -------------------------
    # Attach calculated fields
    # -------------------------
    item["price"] = base_price
    item["original_price"] = original_price
    item["discount_percentage"] = discount_percentage
    item["is_on_sale"] = is_on_sale

    return item
