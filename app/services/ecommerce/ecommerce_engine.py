from datetime import datetime, date
from typing import Dict, Any, Optional
from zoneinfo import ZoneInfo


class EcommerceEngine:

    # ---------------------------------------------
    # CONFIG — Set Your Business Timezone Here
    # ---------------------------------------------
    BUSINESS_TIMEZONE = "UTC"  # Change to "Asia/Dubai" if needed

    # ---------------------------------------------
    # Helpers
    # ---------------------------------------------

    @staticmethod
    def _to_int(value) -> int:
        try:
            return int(value)
        except (TypeError, ValueError):
            return 0

    @staticmethod
    def _to_float(value) -> Optional[float]:
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _parse_date(value) -> Optional[date]:
        """
        Supports:
        - date object
        - datetime object
        - YYYY-MM-DD
        - YYYY-MM-DD HH:MM:SS
        - DD-MM-YYYY (ERP format)
        """

        if not value:
            return None

        if isinstance(value, date):
            return value

        if isinstance(value, datetime):
            return value.date()

        value_str = str(value).strip()

        formats = [
            "%Y-%m-%d",
            "%Y-%m-%d %H:%M:%S",
            "%d-%m-%Y",
        ]

        for fmt in formats:
            try:
                return datetime.strptime(value_str, fmt).date()
            except Exception:
                continue

        return None

    # ---------------------------------------------
    # Promotion Activation
    # ---------------------------------------------

    @staticmethod
    def _today() -> date:
        return datetime.now(
            ZoneInfo(EcommerceEngine.BUSINESS_TIMEZONE)
        ).date()

    @staticmethod
    def is_promotion_active(item: Dict[str, Any]) -> bool:

        if EcommerceEngine._to_int(item.get("custom_enable_promotion")) != 1:
            return False

        start = EcommerceEngine._parse_date(
            item.get("custom_promotion_start")
        )
        end = EcommerceEngine._parse_date(
            item.get("custom_promotion_end")
        )

        if not start or not end:
            return False

        today = EcommerceEngine._today()

        return start <= today <= end

    # ---------------------------------------------
    # Price Resolver (3 Pricing Modes)
    # ---------------------------------------------

    @staticmethod
    def resolve_price(item: Dict[str, Any]) -> Optional[float]:

        # 1️⃣ FIXED MODE
        if EcommerceEngine._to_int(item.get("custom_fixed_price")) == 1:
            return EcommerceEngine._to_float(
                item.get("custom_ecommerce_price")
            )

        # 2️⃣ MRP MODE
        if EcommerceEngine._to_int(item.get("custom_mrp_rate")) == 1:
            return EcommerceEngine._to_float(
                item.get("custom_mrp_price")
            )

        # 3️⃣ PROMOTION MODE
        if EcommerceEngine.is_promotion_active(item):

            # Promotion price visibility
            if EcommerceEngine._to_int(item.get("custom_promotional_rate")) != 1:
                return None

            # Manual Pricing
            if item.get("custom_promotion_type") == "Manual Pricing":
                return EcommerceEngine._to_float(
                    item.get("custom_promotion_price_manual")
                )

            # Percentage Promotion (ERP calculated)
            return EcommerceEngine._to_float(
                item.get("custom_promotional_price")
            )

        # Default fallback
        return EcommerceEngine._to_float(
            item.get("custom_ecommerce_price")
        )

    # ---------------------------------------------
    # Final API Transformation
    # ---------------------------------------------

    @staticmethod
    def transform_item(item: Dict[str, Any]) -> Dict[str, Any]:

        price = EcommerceEngine.resolve_price(item)

        # Visibility
        is_price_visible = (
            EcommerceEngine._to_int(item.get("custom_show_price")) == 1
        )

        is_image_visible = (
            EcommerceEngine._to_int(item.get("custom_show_image")) == 1
        )

        stock_status = (
            "In Stock"
            if EcommerceEngine._to_int(item.get("custom_show_stock")) == 1
            else "Out of Stock"
        )

        # Promotion UI Data
        is_on_sale = False
        original_price = None
        discount_percentage = 0

        if EcommerceEngine.is_promotion_active(item) and price is not None:

            is_on_sale = True

            # Strike price
            if EcommerceEngine._to_int(
                item.get("custom_show_strike_price")
            ) == 1:
                original_price = EcommerceEngine._to_float(
                    item.get("custom_ecommerce_price")
                )

            # 🔥 Discount only for Percentage type
            if item.get("custom_promotion_type") == "Percentage":
                discount_percentage = (
                    EcommerceEngine._to_float(
                        item.get("custom_promotion_discount_")
                    ) or 0
                )

        return {
            "price": price if is_price_visible else None,
            "original_price": original_price,
            "discount_percentage": discount_percentage,
            "is_on_sale": is_on_sale,
            "is_price_visible": is_price_visible,
            "is_image_visible": is_image_visible,
            "stock_status": stock_status,
            "image": item.get("image") if is_image_visible else None,
        }
