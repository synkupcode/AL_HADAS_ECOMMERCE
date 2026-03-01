import time
from typing import Any, Dict

from app.integrations.erp_client import erp_request


class SiteControl:
    """
    Central control hub for all E-Commerce Settings.
    Source of truth: ERPNext.
    """

    SETTINGS_NAME = "1tk6cucvc9"
    CACHE_TTL = 60  # seconds

    _cache: Dict[str, Any] | None = None
    _last_fetch: float = 0

    # -----------------------------
    # Utilities
    # -----------------------------
    @staticmethod
    def _to_bool(value: Any) -> bool:
        return str(value).strip() in ["1", "true", "True", "YES", "yes"]

    # -----------------------------
    # Core Settings Fetch (Cached)
    # -----------------------------
    @classmethod
    def _get_settings(cls) -> Dict[str, Any]:
        now = time.time()

        if cls._cache and (now - cls._last_fetch) < cls.CACHE_TTL:
            return cls._cache

        response = erp_request(
            method="GET",
            path=f"/api/resource/E-Commerce Settings/{cls.SETTINGS_NAME}",
        )

        cls._cache = response.get("data", {}) or {}
        cls._last_fetch = now

        return cls._cache

    # -----------------------------
    # Store Visibility
    # -----------------------------
    @classmethod
    def get_store_visibility(cls) -> str:
        settings = cls._get_settings()
        return settings.get("e_store_visibility", "Enable")

    @classmethod
    def is_site_frozen(cls) -> bool:
        visibility = cls.get_store_visibility()
        return visibility in ["Maintenance", "Disable"]

    # -----------------------------
    # Integration Controls
    # -----------------------------
    @classmethod
    def is_website_integration_enabled(cls) -> bool:
        settings = cls._get_settings()
        return cls._to_bool(settings.get("website_integration"))

    @classmethod
    def is_item_sync_enabled(cls) -> bool:
        settings = cls._get_settings()
        return cls._to_bool(settings.get("enable_item_sync"))

    @classmethod
    def is_customer_sync_enabled(cls) -> bool:
        settings = cls._get_settings()
        return cls._to_bool(settings.get("enable_customer_sync"))

    @classmethod
    def is_price_visibility_enabled(cls) -> bool:
        settings = cls._get_settings()
        return cls._to_bool(settings.get("enable_price_visibility"))

    # -----------------------------
    # Default Order Settings
    # -----------------------------
    @classmethod
    def get_default_order_type(cls) -> str:
        settings = cls._get_settings()
        return settings.get("default_order_type", "E-Commerce RFQ")

    @classmethod
    def get_default_source_warehouse(cls) -> str:
        settings = cls._get_settings()
        return settings.get("default_source_warehouse")
