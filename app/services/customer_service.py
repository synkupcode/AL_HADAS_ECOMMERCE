from typing import Dict, Any, Optional

from app.integrations.erp_client import erp_request


class CustomerError(ValueError):
    pass


# Allowed values from your ERP Customer form
ALLOWED_CUSTOMER_TYPES = {"Individual", "Company", "Partnership"}


# -------------------------
# INTERNAL HELPERS
# -------------------------

def _normalize_customer_type(value: Optional[str]) -> str:
    """
    Ensures customer_type matches ERP allowed values.
    Defaults safely to 'Individual'.
    """
    if not value:
        return "Individual"

    value = value.strip().capitalize()

    if value not in ALLOWED_CUSTOMER_TYPES:
        return "Individual"

    return value


def _find_customer_by_phone(phone: str) -> Optional[str]:
    """
    Search ERP Customer by custom field 'mobile_number'.
    Returns ERP-generated name if found.
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
    Create new Customer in ERP.
    ERP auto-numbering will generate the customer code.
    Returns ERP-generated name.
    """

    address = payload.get("address") or {}
    contact = payload.get("contact") or {}

    customer_payload = {
        "doctype": "Customer",

        # Core Fields (from your ERP form)
        "customer_name": payload.get("customer_name"),
        "customer_type": _normalize_customer_type(payload.get("customer_type")),
        "custom_vat_registration_number": payload.get("vat_number"),

        # Primary Contact Fields
        "map_to_first_name": contact.get("first_name"),
        "map_to_last_name": contact.get("last_name"),
        "email_address": contact.get("email"),
        "mobile_number": payload.get("phone"),

        # Primary Address Fields
        "address_line1": address.get("address_line1"),
        "address_line2": address.get("address_line2"),
        "pincode": address.get("postal_code"),
        "city": address.get("city"),
        "state": address.get("state"),
        "country": address.get("country"),
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


# -------------------------
# PUBLIC FUNCTIONS
# -------------------------

def get_customer_id_by_phone(phone: str) -> Optional[str]:
    """
    Public lookup function.
    Used by customers API.
    Does NOT create customer.
    """
    if not phone:
        raise CustomerError("Phone number is required")

    return _find_customer_by_phone(phone)


def get_or_create_customer(payload: Dict[str, Any]) -> str:
    """
    Used by checkout flow.
    Ensures customer exists in ERP.
    Returns ERP auto-generated customer ID.
    """

    phone = payload.get("phone")
    if not phone:
        raise CustomerError("Phone number is required")

    # 1️⃣ Try to find existing customer
    existing = _find_customer_by_phone(phone)
    if existing:
        return existing

    # 2️⃣ Create new customer
    return _create_customer(payload)
