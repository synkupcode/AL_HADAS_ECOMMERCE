from typing import Dict, Any

def apply_visibility_rules(item: Dict[str, Any]) -> Dict[str, Any]:
    """
    Apply ecommerce tab visibility rules to an ERP item.
    Controls:
    - Show price
    - Show image
    - Stock status (manual)
    """
    # -------------------------
    # Visibility defaults
    # -------------------------
    is_price_visible = bool(item.get("custom_show_price", 0))
    is_image_visible = bool(item.get("custom_show_image", 0))

    # Stock status controlled manually by internal team
    stock_status = "In Stock" if item.get("custom_show_stock", 1) else "Out of Stock"

    # -------------------------
    # Attach to item dict
    # -------------------------
    item["is_price_visible"] = is_price_visible
    item["is_image_visible"] = is_image_visible
    item["stock_status"] = stock_status

    return item
