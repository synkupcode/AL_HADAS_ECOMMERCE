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
    # DOCTYPE (RFQ)
    # -------------------------
    ECOM_RFQ_DOCTYPE: str = "E-Commerce RFQ"
    ECOM_RFQ_ITEM_TABLE_FIELD: str = "item_table"

    # -------------------------
    # CONTACT / ENQUIRY
    # -------------------------
    SALES_EMAIL: str = os.getenv("SALES_EMAIL", "sales@alhadasksa.com")

        # -------------------------
    # JWT AUTHENTICATION
    # -------------------------
    
    JWT_SECRET: str = os.getenv("JWT_SECRET", "")
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(
        os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "15")
    )
    
    REFRESH_TOKEN_EXPIRE_DAYS: int = int(
        os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "30")
    )


settings = Settings()
