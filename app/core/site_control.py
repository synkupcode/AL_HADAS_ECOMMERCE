# app/core/site_control.py

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
        """
        Convert ERP setting value to boolean.
        Handles "Yes"/"No" explicitly.
        """
        if isinstance(value, str):
            return value.strip().lower() == "yes"
        return bool(value)

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

    # -----------------------------
    # Inventory Controls
    # -----------------------------
    @classmethod
    def is_minus_stock_selling_enabled(cls) -> bool:
        settings = cls._get_settings()
        return cls._to_bool(settings.get("enable_minus_stock_selling"))

    @classmethod
    def is_available_quantity_visible(cls) -> bool:
        settings = cls._get_settings()
        return cls._to_bool(settings.get("show_available_quantity"))

    # -----------------------------
    # NEW: SO Auto Submission
    # -----------------------------
    @classmethod
    def is_so_auto_submission_enabled(cls) -> bool:
        """
        Returns True if 'SO Auto Submission' is enabled in E-Commerce Settings.
        Reads "Yes"/"No" directly.
        """
        settings = cls._get_settings()
        return cls._to_bool(settings.get("so_auto_submission"))
