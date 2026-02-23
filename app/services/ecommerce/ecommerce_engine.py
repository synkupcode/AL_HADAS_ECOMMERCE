from datetime import date
from typing import Dict, Any


class EcommerceEngine:

    @staticmethod
    def is_promotion_active(item: Dict[str, Any]) -> bool:
        if item.get("custom_enable_promotion") != 1:
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
        # FIXED MODE
        # -------------------------
        if item.get("custom_fixed_price") == 1:
            return item.get("custom_ecommerce_price")

        # -------------------------
        # MRP MODE
        # -------------------------
        if item.get("custom_mrp_rate") == 1:
            return item.get("custom_mrp_price")

        # -------------------------
        # PROMOTION MODE
        # -------------------------
        if EcommerceEngine.is_promotion_active(item):

            # Price visibility in promotion
            if item.get("custom_promotional_rate") != 1:
                return None  # hide price

            # Promotion type selection
            if item.get("custom_promotion_type") == "Manual Pricing":
                return item.get("custom_promotion_price_manual")

            return item.get("custom_promotional_price")

        # -------------------------
        # DEFAULT FALLBACK
        # -------------------------
        return item.get("custom_ecommerce_price")

    @staticmethod
    def transform_item(item: Dict[str, Any]) -> Dict[str, Any]:

        # Price
        price = EcommerceEngine.resolve_price(item)

        # Visibility
        is_price_visible = item.get("custom_show_price") == 1
        is_image_visible = item.get("custom_show_image") == 1

        # Stock (manual)
        stock_status = "In Stock" if item.get("custom_show_stock") == 1 else "Out of Stock"

        # Strike Price
        show_strike = item.get("custom_show_strike_price") == 1

        original_price = None
        discount_percentage = 0
        is_on_sale = False

        if EcommerceEngine.is_promotion_active(item) and price is not None:
            is_on_sale = True
            original_price = item.get("custom_ecommerce_price")
            discount_percentage = item.get("custom_promotion_discount_") or 0

        response = {
            "price": price if is_price_visible else None,
            "original_price": original_price if show_strike else None,
            "discount_percentage": discount_percentage if show_strike else 0,
            "is_on_sale": is_on_sale,
            "is_price_visible": is_price_visible,
            "is_image_visible": is_image_visible,
            "stock_status": stock_status,
            "image": item.get("image") if is_image_visible else None,
        }

        return response
