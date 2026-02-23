from typing import Dict, Any
from app.integrations.erp_client import erp_request


class CustomerError(ValueError):
    pass


def _create_customer(payload: Dict[str, Any]) -> str:

    customer_payload = {
        "doctype": "Customer",
        "customer_name": payload.get("customer_name"),
        "customer_type": payload.get("customer_type") or "Individual",
        "customer_group": payload.get("customer_group") or "Individual",
        "territory": payload.get("territory") or "All Territories",
    }

    res = erp_request(
        "POST",
        "/api/resource/Customer",
        json=customer_payload,
    )

    customer = res.get("data") or {}
    customer_id = customer.get("name")

    if not customer_id:
        raise CustomerError("Customer creation failed")

    return customer_id


def _create_contact(customer_id: str, payload: Dict[str, Any]) -> None:

    phone = payload.get("phone")
    contact_info = payload.get("contact") or {}

    if not phone and not contact_info:
        return

    contact_payload = {
        "doctype": "Contact",
        "first_name": contact_info.get("first_name") or payload.get("customer_name"),
        "email_ids": [
            {
                "email_id": contact_info.get("email"),
                "is_primary": 1
            }
        ] if contact_info.get("email") else [],
        "phone_nos": [
            {
                "phone": phone,
                "is_primary_mobile": 1
            }
        ] if phone else [],
        "links": [
            {
                "link_doctype": "Customer",
                "link_name": customer_id
            }
        ]
    }

    # Remove empty lists
    contact_payload = {k: v for k, v in contact_payload.items() if v}

    erp_request(
        "POST",
        "/api/resource/Contact",
        json=contact_payload,
    )


def get_or_create_customer(payload: Dict[str, Any]) -> str:

    if not payload.get("customer_name"):
        raise CustomerError("Customer name is required")

    # Create Customer
    customer_id = _create_customer(payload)

    # Create Contact (if phone exists)
    _create_contact(customer_id, payload)

    return customer_id
