
from typing import Dict, Any
from app.integrations.erp_client import erp_request

class CustomerError(ValueError):
    pass


ALLOWED_CUSTOMER_TYPES = {"Individual", "Company", "Partnership"}


def _normalize_customer_type(value: str | None) -> str:
    if not value:
        return "Individual"
    value = value.strip().capitalize()
    if value not in ALLOWED_CUSTOMER_TYPES:
        return "Individual"
    return value


def _find_existing_customer(customer_name: str, phone: str | None) -> str | None:
    """
    Check ERP for an existing customer by name + phone.
    Returns customer_id if exists, else None.
    """
    filters = [["customer_name", "=", customer_name]]
    if phone:
        filters.append(["phone_nos", "like", f"%{phone}%"])

    params = {
        "filters": json.dumps(filters),
        "fields": '["name"]',
        "limit_page_length": 1,
    }

    res = erp_request("GET", "/api/resource/Customer", params=params)
    data = res.get("data") or []
    if data:
        return data[0].get("name")
    return None


# -----------------------------
# CREATE CUSTOMER
# -----------------------------
def create_customer(payload: Dict[str, Any]) -> str:
    """
    Creates a new customer if it does not exist.
    Uses deduplication via name + phone.
    """
    customer_name = payload.get("customer_name")
    phone = payload.get("phone")

    # Check existing customer
    existing_id = _find_existing_customer(customer_name, phone)
    if existing_id:
        return existing_id

    customer_payload = {
        "doctype": "Customer",
        "customer_name": customer_name,
        "customer_type": _normalize_customer_type(payload.get("customer_type")),
        "customer_group": payload.get("customer_group") or "Individual",
        "territory": payload.get("territory") or "All Territories",
        "custom_vat_registration_number": payload.get("vat_number"),
    }

    customer_payload = {k: v for k, v in customer_payload.items() if v not in (None, "")}

    res = erp_request("POST", "/api/resource/Customer", json=customer_payload)
    doc = res.get("data") or {}
    customer_id = doc.get("name")

    if not customer_id:
        raise CustomerError("Customer creation failed")

    return customer_id


# -----------------------------
# CREATE CONTACT
# -----------------------------
def create_contact(customer_id: str, payload: Dict[str, Any]) -> None:
    phone = payload.get("phone")
    contact = payload.get("contact") or {}

    if not phone and not contact:
        return

    contact_payload = {
        "doctype": "Contact",
        "first_name": contact.get("first_name") or payload.get("customer_name"),
        "email_ids": [{"email_id": contact.get("email"), "is_primary": 1}] if contact.get("email") else [],
        "phone_nos": [{"phone": phone, "is_primary_mobile": 1}] if phone else [],
        "links": [{"link_doctype": "Customer", "link_name": customer_id}]
    }

    contact_payload = {k: v for k, v in contact_payload.items() if v}
    erp_request("POST", "/api/resource/Contact", json=contact_payload)


# -----------------------------
# MAIN FUNCTION
# -----------------------------
def get_or_create_customer(payload: Dict[str, Any]) -> str:
    if not payload.get("customer_name"):
        raise CustomerError("Customer name is required")

    customer_id = create_customer(payload)
    create_contact(customer_id, payload)

    return customer_id
