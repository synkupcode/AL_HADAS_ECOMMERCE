import time
from typing import Any, Dict

from app.integrations.erp_client import erp_request


class SiteControl:
    """
    Central control hub for all E-Commerce Settings.
    Source of truth: ERPNext.
    """

    SETTINGS_NAME = "1tk6cucvc9"
    CACHE_TTL = 60  # seconds (production-safe)

    _cache: Dict[str, Any] | None = None
    _last_fetch: float = 0

    # -----------------------------------
    # Core Settings Fetch (With Cache)
    # -----------------------------------
    @classmethod
    def _get_settings(cls) -> Dict[str, Any]:

        now = time.time()

        if cls._cache and (now - cls._last_fetch) < cls.CACHE_TTL:
            return cls._cache

        response = erp_request(
            method="GET",
            path=f"/api/resource/E-Commerce Settings/{cls.SETTINGS_NAME}",
        )

        cls._cache = response.get("data", {})
        cls._last_fetch = now

        return cls._cache

    # -----------------------------------
    # Tab 1 — Store Visibility
    # -----------------------------------
    @classmethod
    def get_store_visibility(cls) -> str:
        settings = cls._get_settings()
        return settings.get("e_store_visibility", "Enable")

    @classmethod
    def is_site_frozen(cls) -> bool:
        """
        Returns True if site should be frozen
        (Maintenance or Disable)
        """
        visibility = cls.get_store_visibility()
        return visibility in ["Maintenance", "Disable"]
