from typing import Dict, List, Tuple
from datetime import datetime, timedelta

from app.core.site_control import SiteControl
from app.integrations.erp_client import erp_request


class StockService:

    # -----------------------------------
    # Reservation configuration
    # -----------------------------------
    RESERVATION_TIMEOUT_MINUTES = 10

    # item_code → [(qty, timestamp)]
    RESERVED_STOCK: Dict[str, List[Tuple[float, datetime]]] = {}

    # -----------------------------------
    # CLEAN EXPIRED RESERVATIONS
    # -----------------------------------
    @classmethod
    def _cleanup_expired(cls):

        now = datetime.utcnow()
        timeout = timedelta(minutes=cls.RESERVATION_TIMEOUT_MINUTES)

        for item_code in list(cls.RESERVED_STOCK.keys()):

            valid_entries = []

            for qty, ts in cls.RESERVED_STOCK[item_code]:

                if now - ts < timeout:
                    valid_entries.append((qty, ts))

            if valid_entries:
                cls.RESERVED_STOCK[item_code] = valid_entries
            else:
                del cls.RESERVED_STOCK[item_code]

    # -----------------------------------
    # GET RESERVED QUANTITY
    # -----------------------------------
    @classmethod
    def _get_reserved_qty(cls, item_code: str) -> float:

        cls._cleanup_expired()

        entries = cls.RESERVED_STOCK.get(item_code, [])

        return sum(qty for qty, _ in entries)

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

        bins = res.get("data", []) or []

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
            return {"stock_status": "Unavailable"}

        item_code = item.get("item_code")

        available = stock_map.get(item_code, 0)

        # subtract reserved quantities
        reserved_local = cls._get_reserved_qty(item_code)

        available -= reserved_local

        if available <= 0:

            if SiteControl.is_minus_stock_selling_enabled():
                return {"stock_status": "Backorder"}

            return {"stock_status": "Out of Stock"}

        result = {"stock_status": "In Stock"}

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

            reserved_local = cls._get_reserved_qty(item_code)

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

        now = datetime.utcnow()

        for item in cart_items:

            item_code = item.get("item_code")
            qty = float(item.get("qty") or 0)

            cls.RESERVED_STOCK.setdefault(item_code, []).append((qty, now))

    # -----------------------------------
    # Release reservation
    # -----------------------------------
    @classmethod
    def release_reservation(cls, cart_items):

        cls._cleanup_expired()

        for item in cart_items:

            item_code = item.get("item_code")
            qty = float(item.get("qty") or 0)

            entries = cls.RESERVED_STOCK.get(item_code)

            if not entries:
                continue

            remaining = qty
            updated = []

            for q, ts in entries:

                if remaining <= 0:
                    updated.append((q, ts))
                    continue

                if q <= remaining:
                    remaining -= q
                else:
                    updated.append((q - remaining, ts))
                    remaining = 0

            if updated:
                cls.RESERVED_STOCK[item_code] = updated
            else:
                del cls.RESERVED_STOCK[item_code]
