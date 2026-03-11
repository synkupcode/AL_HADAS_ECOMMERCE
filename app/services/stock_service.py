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
            valid_entries = [
                (qty, ts) for qty, ts in cls.RESERVED_STOCK[item_code]
                if now - ts < timeout
            ]
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
            item_code = b.get("item_code")
            try:
                actual = float(b.get("actual_qty") or 0)
                reserved = float(b.get("reserved_qty") or 0)
                available = max(actual - reserved, 0)
            except Exception:
                available = 0
            if item_code:
                stock_map[item_code] = available

        return stock_map

    # -----------------------------------
    # Resolve stock status for product API
    # -----------------------------------
    @classmethod
    def resolve_stock_status(cls, item, stock_map):
        item_code = item.get("item_code")
        show_stock_item = int(item.get("custom_show_stock") or 0)
        show_quantity_global = SiteControl.is_available_qty_enabled()
        minus_stock_allowed = SiteControl.is_minus_stock_selling_enabled()

        # Get available stock safely
        try:
            available = float(stock_map.get(item_code, 0)) - cls._get_reserved_qty(item_code)
        except Exception:
            available = 0
        available = max(available, 0)

        # Determine stock_status
        if not show_stock_item:
            stock_status = "Out of Stock"
        elif available <= 0:
            stock_status = "Backorder" if minus_stock_allowed else "Out of Stock"
        else:
            stock_status = "In Stock"

        result = {"stock_status": stock_status}

        # Include available_qty only if allowed and stock > 0
        if show_stock_item and show_quantity_global and available > 0:
            result["available_qty"] = int(available)

        return result

    # -----------------------------------
    # Validate cart stock
    # -----------------------------------
    @classmethod
    def validate_cart_stock(cls, cart_items):
        item_codes = [item.get("item_code") for item in cart_items]
        stock_map = cls.fetch_stock_map(item_codes)
        minus_stock_allowed = SiteControl.is_minus_stock_selling_enabled()

        for item in cart_items:
            item_code = item.get("item_code")
            qty = float(item.get("qty") or 0)
            try:
                available = float(stock_map.get(item_code, 0)) - cls._get_reserved_qty(item_code)
            except Exception:
                available = 0

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
