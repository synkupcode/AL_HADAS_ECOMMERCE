from datetime import date
from typing import Dict, Any


def _is_enabled(value) -> bool:
    return str(value) == "1"


class EcommerceEngine:

    @staticmethod
    def is_promotion_active(item: Dict[str, Any]) -> bool:
        if not _is_enabled(item.get("custom_enable_promotion")):
            return False

        today = date.today()
        start = item.get("custom_promotion_start")
        end = item.get("custom_promotion_end")

        if not start or not end:
            return False

        return start <= today <= end

    @staticmethod
    def resolve_price(item: Dict[str, Any]):

        # -------------------------
        # PROMOTION MODE (Priority 1)
        # -------------------------
        if EcommerceEngine.is_promotion_active(item):

            if not _is_enabled(item.get("custom_promotional_rate")):
                return None

            if item.get("custom_promotion_type") == "Manual Pricing":
                return item.get("custom_promotion_price_manual")

            return item.get("custom_promotional_price")

        # -------------------------
        # FIXED MODE (Priority 2)
        # -------------------------
        if _is_enabled(item.get("custom_fixed_price")):
            return item.get("custom_ecommerce_price")

        # -------------------------
        # MRP MODE (Priority 3)
        # -------------------------
        if _is_enabled(item.get("custom_mrp_rate")):
            return item.get("custom_mrp_price")

        # -------------------------
        # DEFAULT
        # -------------------------
        return item.get("custom_ecommerce_price")

    @staticmethod
    def transform_item(item: Dict[str, Any]) -> Dict[str, Any]:

        price = EcommerceEngine.resolve_price(item)

        is_price_visible = _is_enabled(item.get("custom_show_price"))
        is_image_visible = _is_enabled(item.get("custom_show_image"))
        show_strike = _is_enabled(item.get("custom_show_strike_price"))

        stock_status = (
            "In Stock"
            if _is_enabled(item.get("custom_show_stock"))
            else "Out of Stock"
        )

        original_price = None
        discount_percentage = 0
        is_on_sale = False

        # Strike price logic
        if EcommerceEngine.is_promotion_active(item) and price is not None:
            is_on_sale = True

            base_type = item.get("custom_promotion_base_price")

            if base_type == "Standard":
                original_price = item.get("custom_standard_selling_price")
            else:
                original_price = item.get("custom_ecommerce_price")

            discount_percentage = item.get("custom_promotion_discount_") or 0

        return {
            "price": price if is_price_visible else None,
            "original_price": original_price if show_strike else None,
            "discount_percentage": discount_percentage if show_strike else 0,
            "is_on_sale": is_on_sale,
            "is_price_visible": is_price_visible,
            "is_image_visible": is_image_visible,
            "stock_status": stock_status,
            "image": item.get("image") if is_image_visible else None,
        }
