from typing import Dict, Any, Optional
from app.core.config import settings
from app.integrations.erp_client import erp_request


class CustomerError(ValueError):
    pass


ALLOWED_CUSTOMER_TYPES = {"Individual", "Company", "Partnership"}


def _normalize_customer_type(value: Optional[str]) -> str:
    if not value:
        return "Individual"

    value = value.strip().capitalize()

    if value not in ALLOWED_CUSTOMER_TYPES:
        return "Individual"

    return value


def _create_customer(payload: Dict[str, Any]) -> str:
    """
    Create Customer using standard ERPNext structure.
    Phone and Address must be handled via Contact and Address doctypes.
    """

    customer_payload = {
        "doctype": "Customer",
        "customer_name": payload.get("customer_name"),
        "customer_type": _normalize_customer_type(payload.get("customer_type")),
        "customer_group": payload.get("customer_group") or "Individual",
        "territory": payload.get("territory") or "All Territories",
        "custom_vat_registration_number": payload.get("vat_number"),
    }

    # Remove empty values
    customer_payload = {
        k: v for k, v in customer_payload.items()
        if v not in (None, "")
    }

    res = erp_request(
        "POST",
        "/api/resource/Customer",
        json=customer_payload,
    )

    doc = res.get("data") or {}
    customer_id = doc.get("name")

    if not customer_id:
        raise CustomerError("Customer creation failed")

    return customer_id


def get_or_create_customer(payload: Dict[str, Any]) -> str:
    """
    Professional approach:
    Always create customer cleanly.
    Duplicate checking can be implemented later using other logic if needed.
    """

    if not payload.get("customer_name"):
        raise CustomerError("Customer name is required")

    return _create_customer(payload)
