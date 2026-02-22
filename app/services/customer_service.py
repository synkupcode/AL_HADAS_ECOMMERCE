from typing import Dict, Any, Optional

from app.integrations.erp_client import erp_request
from app.core.config import settings


class CustomerError(ValueError):
    pass


def _find_customer_by_phone(phone: str) -> Optional[str]:
    """
    Search Customer by mobile_number (custom ERP field).
    Returns ERP name if found.
    """

    filters = [
        ["Customer", "mobile_number", "=", phone]
    ]

    res = erp_request(
        "GET",
        "/api/resource/Customer",
        params={
            "filters": str(filters),
            "fields": '["name"]'
        },
    )

    data = res.get("data") or []
    if data:
        return data[0]["name"]

    return None


def _create_customer(payload: Dict[str, Any]) -> str:
    """
    Create new Customer in ERP using your custom field structure.
    Returns ERP auto-generated name.
    """

    address = payload.get("address") or {}
    contact = payload.get("contact") or {}

    customer_payload = {
        "doctype": "Customer",

        # Core
        "customer_name": payload.get("customer_name"),
        "customer_type": payload.get("customer_type") or "Individual",
        "customer_group": "Commercial",     # Must match ERP exactly
        "territory": "Saudi Arabia",        # Must match ERP exactly

        # Custom VAT field
        "custom_vat_registration_number": payload.get("vat_number"),

        # Contact mapping (custom ERP fields)
        "map_to_first_name": contact.get("first_name"),
        "map_to_last_name": contact.get("last_name"),
        "email_address": contact.get("email"),
        "mobile_number": payload.get("phone"),

        # Address mapping (custom ERP fields)
        "address_line1": address.get("address_line1"),
        "address_line2": address.get("street_name"),
        "pincode": address.get("postal_code"),
        "city": address.get("city"),
        "state": address.get("state"),
        "country": address.get("country"),
    }

    # Remove None values
    customer_payload = {k: v for k, v in customer_payload.items() if v is not None}

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
    Ensures customer exists.
    Returns ERP customer name (auto-numbered).
    """

    phone = payload.get("phone")
    if not phone:
        raise CustomerError("Phone is required")

    # 1️⃣ Try find existing
    existing = _find_customer_by_phone(phone)
    if existing:
        return existing

    # 2️⃣ Create new
    return _create_customer(payload)
