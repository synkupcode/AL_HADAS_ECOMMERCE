import json
from typing import Dict, Any
from app.integrations.erp_client import erp_request

class CustomerError(ValueError):
    pass

def create_customer(payload: Dict[str, Any]) -> str:
    customer_payload = {
        "doctype": "Customer",
        "customer_name": payload.get("customer_name"),
        "customer_type": payload.get("customer_type", "Individual"),
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
        "links": [{"link_doctype": "Customer", "link_name": customer_id}],
    }
    contact_payload = {k: v for k, v in contact_payload.items() if v}
    erp_request("POST", "/api/resource/Contact", json=contact_payload)

def get_or_create_customer(payload: Dict[str, Any]) -> str:
    customer_name = payload.get("customer_name")
    phone_number = payload.get("phone")
    if not customer_name:
        raise CustomerError("Customer name is required")

    # Check existing customer
    filters = [["customer_name", "=", customer_name]]
    if phone_number:
        filters.append(["phone_number", "=", phone_number])

    res = erp_request("GET", "/api/resource/Customer",
                      params={"filters": json.dumps(filters), "fields": '["name"]'})
    data = res.get("data") or []
    if data:
        customer_id = data[0]["name"]
    else:
        customer_id = create_customer(payload)

    create_contact(customer_id, payload)
    return customer_id
