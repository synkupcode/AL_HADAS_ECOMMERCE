from datetime import date, datetime
from typing import Dict, Any


def _is_enabled(value) -> bool:
    """
    ERP checkbox safety:
    Handles 1, "1", True safely.
    """
    return str(value) == "1"


class EcommerceEngine:

    # -------------------------------------------------
    # PROMOTION CHECK
    # -------------------------------------------------
    @staticmethod
    def is_promotion_active(item: Dict[str, Any]) -> bool:
        if not _is_enabled(item.get("custom_enable_promotion")):
            return False

        today = date.today()

        start_raw = item.get("custom_promotion_start")
        end_raw = item.get("custom_promotion_end")

        if not start_raw or not end_raw:
            return False

        try:
            # ERP returns date fields as string "YYYY-MM-DD"
            start = datetime.strptime(start_raw, "%Y-%m-%d").date()
            end = datetime.strptime(end_raw, "%Y-%m-%d").date()
        except Exception:
            return False  # Fail safe if format unexpected

        return start <= today <= end

    # -------------------------------------------------
    # PRICE RESOLUTION
    # -------------------------------------------------
    @staticmethod
    def resolve_price(item: Dict[str, Any]):

        # 1️⃣ PROMOTION MODE (Highest Priority)
        if EcommerceEngine.is_promotion_active(item):

            # Promotion must allow showing price
            if not _is_enabled(item.get("custom_promotional_rate")):
                return None

            # Manual or ERP calculated
            if item.get("custom_promotion_type") == "Manual Pricing":
                return item.get("custom_promotion_price_manual")

            return item.get("custom_promotional_price")

        # 2️⃣ FIXED MODE
        if _is_enabled(item.get("custom_fixed_price")):
            return item.get("custom_ecommerce_price")

        # 3️⃣ MRP MODE
        if _is_enabled(item.get("custom_mrp_rate")):
            return item.get("custom_mrp_price")

        # 4️⃣ DEFAULT FALLBACK
        return item.get("custom_ecommerce_price")

    # -------------------------------------------------
    # TRANSFORM ITEM FOR FRONTEND
    # -------------------------------------------------
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

        # Strike price logic (only when promotion active)
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
