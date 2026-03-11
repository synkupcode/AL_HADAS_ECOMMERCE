from typing import Dict, List

from app.core.site_control import SiteControl
from app.integrations.erp_client import erp_request


class StockService:

    @staticmethod
    def _calculate_available_qty(bin_row: dict) -> float:
        actual = float(bin_row.get("actual_qty") or 0)
        reserved = float(bin_row.get("reserved_qty") or 0)
        return actual - reserved

    @classmethod
    def fetch_stock_map(cls, item_codes: List[str]) -> Dict[str, float]:

        if not item_codes:
            return {}

        warehouse = SiteControl.get_default_source_warehouse()

        filters = [
            ["item_code", "in", item_codes],
        ]

        if warehouse:
            filters.append(["warehouse", "=", warehouse])

        params = {
            "filters": str(filters).replace("'", '"'),
            "fields": '["item_code","actual_qty","reserved_qty"]',
            "limit_page_length": len(item_codes),
        }

        response = erp_request(
            "GET",
            "/api/resource/Bin",
            params=params,
        )

        bins = response.get("data", []) or []

        stock_map: Dict[str, float] = {}

        for row in bins:
            item_code = row.get("item_code")
            stock_map[item_code] = cls._calculate_available_qty(row)

        return stock_map
