import os
from dotenv import load_dotenv

load_dotenv()


def _split_csv(value: str) -> list[str]:
    return [v.strip() for v in (value or "").split(",") if v.strip()]


class Settings:
    # -------------------------
    # ERP CONFIGURATION
    # -------------------------
    ERP_BASE_URL: str = os.getenv("ERP_BASE_URL", "").rstrip("/")
    ERP_API_KEY: str = os.getenv("ERP_API_KEY", "")
    ERP_API_SECRET: str = os.getenv("ERP_API_SECRET", "")

    # -------------------------
    # CORS
    # -------------------------
    ALLOWED_ORIGINS: list[str] = _split_csv(
        os.getenv("ALLOWED_ORIGINS", "*")
    )

    # -------------------------
    # FRONTEND SECURITY
    # -------------------------
    FRONTEND_SECRET_TOKEN: str = os.getenv("FRONTEND_SECRET_TOKEN", "")

    # -------------------------
    # DOCTYPE
    # -------------------------
    ECOM_RFQ_DOCTYPE: str = "E-Commerce RFQ"

    # -------------------------
    # ITEM TABLE FIELD
    # -------------------------
    ECOM_RFQ_ITEM_TABLE_FIELD: str = "item_table"


settings = Settings()
