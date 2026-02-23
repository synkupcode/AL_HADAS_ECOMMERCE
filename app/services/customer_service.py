from typing import Dict, Any, Optional
import json
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


def _find_customer_by_phone(phone: str) -> Optional[str]:
    filters = [settings.CUSTOMER_PHONE_FIELD, "=", phone]

    res = erp_request(
        "GET",
        "/api/resource/Customer",
        params={
            "filters": json.dumps(filters),
            "fields": json.dumps(["name"]),
        },
    )

    data = res.get("data") or []
    if data:
        return data[0]["name"]

    return None


def _create_customer(payload: Dict[str, Any]) -> str:

    address = payload.get("address") or {}
    contact = payload.get("contact") or {}

    customer_payload = {
        "doctype": "Customer",
        "customer_name": payload.get("customer_name"),
        "customer_type": _normalize_customer_type(payload.get("customer_type")),
        "custom_vat_registration_number": payload.get("vat_number"),
        "map_to_first_name": contact.get("first_name"),
        "map_to_last_name": contact.get("last_name"),
        "email_address": contact.get("email"),
        "number": payload.get("phone"),
        "address_line1": address.get("address_line1"),
        "address_line2": address.get("address_line2"),
        "pincode": address.get("postal_code"),
        "city": address.get("city"),
        "state": address.get("state"),
        "country": address.get("country"),
    }

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

    phone = payload.get("phone")
    if not phone:
        raise CustomerError("Phone number required")

    existing = _find_customer_by_phone(phone)
    if existing:
        return existing

    return _create_customer(payload)
