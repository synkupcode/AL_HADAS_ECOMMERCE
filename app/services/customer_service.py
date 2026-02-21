import json
from typing import Any, Dict, Optional

from app.core.config import settings
from app.integrations.erp_client import erp_request
from app.utils.validators import require_keys


def get_customer_id_by_phone(phone: str) -> Optional[str]:
    phone = (phone or "").strip()
    if not phone:
        return None

    filters = [[settings.CUSTOMER_PHONE_FIELD, "=", phone]]
    params = {
        "filters": json.dumps(filters),
        "fields": json.dumps(["name"]),
        "limit_page_length": 1,
    }
    res = erp_request("GET", "/api/resource/Customer", params=params)
    rows = res.get("data", []) or []
    return rows[0]["name"] if rows else None


def get_or_create_customer(payload: Dict[str, Any]) -> str:
    """
    Uses EXACT inputs from your Frappe logic:
      phone, customer_name, customer_type, vat_number, address, contact
    """
    phone = (payload.get("phone") or "").strip()
    if not phone:
        raise ValueError("Phone number is required")

    existing = get_customer_id_by_phone(phone)
    if existing:
        return existing

    # New customer: enforce mandatory fields exactly like your code
    require_keys(payload, ["customer_name", "customer_type", "vat_number", "address", "contact"])

    address = payload.get("address") or {}
    contact = payload.get("contact") or {}

    # Create Customer
    cust_payload = {
        "customer_name": payload.get("customer_name"),
        "customer_type": payload.get("customer_type") or "Individual",
        "customer_group": "Commercial",
        "territory": "KSA",
        "tax_id": payload.get("vat_number"),
        "phone": phone,
        "customer_email": contact.get("email") if isinstance(contact, dict) else None,
    }
    cust_res = erp_request("POST", "/api/resource/Customer", json=cust_payload)
    customer_id = (cust_res.get("data") or {}).get("name")
    if not customer_id:
        raise Exception("Customer creation failed (no name returned)")

    # Create Address (linked)
    erp_request("POST", "/api/resource/Address", json={
        "address_title": payload.get("customer_name"),
        "address_line1": address.get("address_line1"),
        "city": address.get("city"),
        "country": address.get("country"),
        "pincode": address.get("postal_code"),
        "address_type": address.get("address_type", "Billing"),
        "links": [{"link_doctype": "Customer", "link_name": customer_id}]
    })

    # Create Contact (linked)
    erp_request("POST", "/api/resource/Contact", json={
        "first_name": contact.get("first_name"),
        "email_id": contact.get("email"),
        "phone": contact.get("phone") or phone,
        "links": [{"link_doctype": "Customer", "link_name": customer_id}]
    })

    return customer_id