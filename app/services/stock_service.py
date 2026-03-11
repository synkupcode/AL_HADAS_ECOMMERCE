from typing import Dict, List

from app.core.site_control import SiteControl
from app.integrations.erp_client import erp_request


class StockService:

    # -----------------------------------
    # In-memory reservation storage
    # -----------------------------------
    RESERVED_STOCK: Dict[str, float] = {}

    # -----------------------------------
    # Fetch stock for items
    # -----------------------------------
    @classmethod
    def fetch_stock_map(cls, item_codes: List[str]) -> Dict[str, float]:

        if not item_codes:
            return {}

        warehouse = SiteControl.get_default_source_warehouse()

        if not warehouse:
            return {}

        filters = [
            ["item_code", "in", item_codes],
            ["warehouse", "=", warehouse]
        ]

        res = erp_request(
            method="GET",
            path="/api/resource/Bin",
            params={
                "fields": '["item_code","actual_qty","reserved_qty"]',
                "filters": str(filters).replace("'", '"'),
                "limit_page_length": len(item_codes)
            }
        )

        bins = res.get("data", []) or {}

        stock_map = {}

        for b in bins:

            actual = float(b.get("actual_qty") or 0)
            reserved = float(b.get("reserved_qty") or 0)

            available = actual - reserved

            stock_map[b["item_code"]] = max(available, 0)

        return stock_map

    # -----------------------------------
    # Resolve stock status for product API
    # -----------------------------------
    @classmethod
    def resolve_stock_status(cls, item, stock_map):

        show_stock = int(item.get("custom_show_stock") or 0)

        if show_stock != 1:
            return {
                "stock_status": "Unavailable"
            }

        item_code = item.get("item_code")

        available = stock_map.get(item_code, 0)

        # subtract reservations
        reserved_local = cls.RESERVED_STOCK.get(item_code, 0)
        available -= reserved_local

        if available <= 0:

            if SiteControl.is_minus_stock_selling_enabled():
                return {"stock_status": "Backorder"}

            return {"stock_status": "Out of Stock"}

        result = {
            "stock_status": "In Stock"
        }

        if SiteControl.is_available_qty_enabled():
            result["available_qty"] = int(available)

        return result

    # -----------------------------------
    # Validate cart stock
    # -----------------------------------
    @classmethod
    def validate_cart_stock(cls, cart_items):

        item_codes = [
            item.get("item_code")
            for item in cart_items
        ]

        stock_map = cls.fetch_stock_map(item_codes)

        minus_stock_allowed = SiteControl.is_minus_stock_selling_enabled()

        for item in cart_items:

            item_code = item.get("item_code")
            qty = float(item.get("qty") or 0)

            available = stock_map.get(item_code, 0)

            reserved_local = cls.RESERVED_STOCK.get(item_code, 0)

            available -= reserved_local

            if available >= qty:
                continue

            if minus_stock_allowed:
                continue

            raise ValueError(
                f"Insufficient stock for item {item_code}. "
                f"Available: {available}, Requested: {qty}"
            )

    # -----------------------------------
    # Reserve stock
    # -----------------------------------
    @classmethod
    def reserve_stock(cls, cart_items):

        for item in cart_items:

            item_code = item.get("item_code")
            qty = float(item.get("qty") or 0)

            cls.RESERVED_STOCK[item_code] = (
                cls.RESERVED_STOCK.get(item_code, 0) + qty
            )

    # -----------------------------------
    # Release reservation
    # -----------------------------------
    @classmethod
    def release_reservation(cls, cart_items):

        for item in cart_items:

            item_code = item.get("item_code")
            qty = float(item.get("qty") or 0)

            if item_code in cls.RESERVED_STOCK:

                cls.RESERVED_STOCK[item_code] -= qty

                if cls.RESERVED_STOCK[item_code] <= 0:
                    del cls.RESERVED_STOCK[item_code]
