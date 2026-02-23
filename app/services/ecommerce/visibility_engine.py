from typing import Dict, Any


def apply_visibility_rules(item: Dict[str, Any]) -> Dict[str, Any]:
    """
    Applies ecommerce visibility rules.
    """

    # Price visibility
    show_price = bool(item.get("custom_show_price"))
    if not show_price:
        item["price"] = None
        item["is_price_visible"] = False
    else:
        item["is_price_visible"] = True

    # Image visibility
    show_image = bool(item.get("custom_show_image"))
    if not show_image:
        item["image"] = None
        item["is_image_visible"] = False
    else:
        item["is_image_visible"] = True

    # Stock visibility (manual control)
    show_stock = bool(item.get("custom_show_stock"))
    item["stock_status"] = "In Stock" if show_stock else "Out of Stock"

    return item
