import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def _split_csv(value: str) -> list[str]:
    return [v.strip() for v in (value or "").split(",") if v.strip()]


class Settings:
    # ERP Configuration
    ERP_BASE_URL: str = os.getenv("ERP_BASE_URL", "").rstrip("/")
    ERP_API_KEY: str = os.getenv("ERP_API_KEY", "")
    ERP_API_SECRET: str = os.getenv("ERP_API_SECRET", "")

    # CORS
    ALLOWED_ORIGINS: list[str] = _split_csv(
        os.getenv("ALLOWED_ORIGINS", "*")
    )

    # Optional Frontend Protection
    FRONTEND_SECRET_TOKEN: str = os.getenv("FRONTEND_SECRET_TOKEN", "")

    # Doctype Names
    ECOM_RFQ_DOCTYPE: str = "E-Commerce RFQ"
    ECOM_RFQ_DOCTYPE_URL: str = "E-Commerce%20RFQ"

    # Item Table Fields
    ECOM_RFQ_ITEM_TABLE_FIELD: str = "item_table"
    ECOM_RFQ_ITEM_ROW_FIELDS = {
        "item_code": "item_code",
        "item_name": "item_name",
        "quantity": "quantity",
        "unit_pricex": "unit_pricex",
        "uom": "uom",
        "amount": "amount",
    }

    # Customer Lookup Field
    CUSTOMER_PHONE_FIELD: str = "phone"


settings = Settings()