# app/core/config.py

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
    # SMTP (Direct Email for OTP)
    # -------------------------
    SMTP_HOST: str = os.getenv("SMTP_HOST", "")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USERNAME: str = os.getenv("SMTP_USERNAME", "")
    SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD", "")
    SMTP_FROM_EMAIL: str = os.getenv("SMTP_FROM_EMAIL", "")
    SMTP_USE_TLS: bool = os.getenv("SMTP_USE_TLS", "true").lower() == "true"

    # -------------------------
    # Other Settings (optional)
    # -------------------------
    SALES_EMAIL: str = os.getenv("SALES_EMAIL", "sales@alhadasksa.com")


settings = Settings()
