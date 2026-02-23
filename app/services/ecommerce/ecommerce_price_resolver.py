from typing import Dict, Any
from datetime import date


class EcommercePriceResolver:

    @staticmethod
    def resolve(item: Dict[str, Any]) -> Dict[str, Any]:
        """
        Takes a raw ERP Item dict
        Returns final ecommerce pricing + visibility info
        """

        # -------------------------
        # PRICE VISIBILITY
        # -------------------------
        is_price_visible = item.get("custom_show_price") == 1

        # -------------------------
        # IMAGE VISIBILITY
        # -------------------------
        is_image_visible = item.get("custom_show_image") == 1

        # -------------------------
        # STOCK STATUS (Manual)
        # -------------------------
        is_in_stock = item.get("custom_show_stock") == 1
        stock_status = "In Stock" if is_in_stock else "Out of Stock"

        # -------------------------
        # BASE PRICE SELECTION
        # -------------------------
        base_price = None

        pricing_mode = item.get("custom_pricing_mode")

        if pricing_mode == "Fixed":
            base_price = item.get("custom_ecommerce_price")

        elif pricing_mode == "MRP":
            base_price = item.get("custom_mrp_price")

        # Fallback
        if base_price is None:
            base_price = item.get("standard_rate", 0)

        # -------------------------
        # PROMOTION LOGIC
        # -------------------------
        final_price = base_price
        original_price = None
        discount_percentage = 0
        is_on_sale = False

        if item.get("custom_enable_promotion") == 1:

            today = date.today()

            start = item.get("custom_promotion_start")
            end = item.get("custom_promotion_end")

            if start and end and start <= today <= end:

                is_on_sale = True

                # ERP already calculates promotional price
                if item.get("custom_promotion_type") == "Manual Pricing":
                    final_price = item.get("custom_promotion_price_manual")

                else:
                    final_price = item.get("custom_promotional_price")

                original_price = base_price
                discount_percentage = item.get("custom_promotion_discount_") or 0

        # -------------------------
        # STRIKE PRICE LOGIC
        # -------------------------
        show_strike = item.get("custom_show_strike_price") == 1

        response = {
            "price": final_price if is_price_visible else None,
            "original_price": original_price if show_strike else None,
            "discount_percentage": discount_percentage,
            "is_on_sale": is_on_sale,
            "is_price_visible": is_price_visible,
            "is_image_visible": is_image_visible,
            "stock_status": stock_status,
            "image": item.get("image") if is_image_visible else None,
        }

        return response
