from typing import Dict, List, Tuple
from datetime import datetime, timedelta

from app.core.site_control import SiteControl
from app.integrations.erp_client import erp_request


class StockService:

    # -----------------------------------
    # Reservation configuration
    # -----------------------------------
    RESERVATION_TIMEOUT_MINUTES = 10
    # Format: item_code → [(qty_reserved, timestamp)]
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
    # FETCH STOCK MAP FROM ERP
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

        response = erp_request(
            method="GET",
            path="/api/resource/Bin",
            params={
                "fields": '["item_code","actual_qty","reserved_qty"]',
                "filters": str(filters).replace("'", '"'),
                "limit_page_length": len(item_codes)
            }
        )

        bins = response.get("data", []) or []
        stock_map: Dict[str, float] = {}

        for b in bins:
            try:
                actual = float(b.get("actual_qty") or 0)
                reserved = float(b.get("reserved_qty") or 0)
                stock_map[b["item_code"]] = max(actual - reserved, 0)
            except (TypeError, ValueError, KeyError):
                stock_map[b.get("item_code", "unknown")] = 0

        return stock_map

    # -----------------------------------
    # RESOLVE STOCK STATUS (aligned with EcommerceEngine)
    # -----------------------------------
    @classmethod
    def resolve_stock_status(cls, item: Dict, stock_map: Dict[str, float]) -> Dict:
        try:
            show_stock = int(item.get("custom_show_stock") or 0)
        except (ValueError, TypeError):
            show_stock = 0

        item_code = item.get("item_code") or "unknown"
        available = float(stock_map.get(item_code, 0))
        reserved_local = cls._get_reserved_qty(item_code)
        available -= reserved_local
        available = max(available, 0)

        result: Dict = {"stock_status": "Out of Stock"}

        if show_stock == 1:
            if available <= 0:
                if SiteControl.is_minus_stock_selling_enabled():
                    result["stock_status"] = "Backorder"
                else:
                    result["stock_status"] = "Out of Stock"
            else:
                result["stock_status"] = "In Stock"
                if SiteControl.is_available_qty_enabled():
                    result["available_qty"] = int(available)

        return result

    # -----------------------------------
    # VALIDATE CART STOCK BEFORE CHECKOUT
    # -----------------------------------
    @classmethod
    def validate_cart_stock(cls, cart_items: List[Dict]):
        item_codes = [item.get("item_code") for item in cart_items]
        stock_map = cls.fetch_stock_map(item_codes)
        minus_stock_allowed = SiteControl.is_minus_stock_selling_enabled()

        for item in cart_items:
            item_code = item.get("item_code")
            qty = float(item.get("qty") or 0)
            available = float(stock_map.get(item_code, 0))
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
    # RESERVE STOCK DURING CHECKOUT
    # -----------------------------------
    @classmethod
    def reserve_stock(cls, cart_items: List[Dict]):
        now = datetime.utcnow()
        for item in cart_items:
            item_code = item.get("item_code")
            qty = float(item.get("qty") or 0)
            cls.RESERVED_STOCK.setdefault(item_code, []).append((qty, now))

    # -----------------------------------
    # RELEASE RESERVED STOCK
    # -----------------------------------
    @classmethod
    def release_reservation(cls, cart_items: List[Dict]):
        cls._cleanup_expired()
        for item in cart_items:
            item_code = item.get("item_code")
            qty = float(item.get("qty") or 0)
            entries = cls.RESERVED_STOCK.get(item_code)
            if not entries:
                continue

            remaining = qty
            updated: List[Tuple[float, datetime]] = []

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
