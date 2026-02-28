from typing import Dict, Any
from app.integrations.erp_client import erp_request


class CustomerError(ValueError):
    pass


def _find_customer_by_phone(phone: str) -> str | None:
    res = erp_request(
        "GET",
        "/api/resource/Customer",
        params={
            "filters": f'[["custom_phone_number","=","{phone}"]]',
            "fields": '["name"]',
            "limit_page_length": 1,
        },
    )

    data = res.get("data") or []
    if data:
        return data[0]["name"]

    return None


def get_or_create_customer(payload: Dict[str, Any]) -> str:
    phone = payload.get("phone")
    if not phone:
        raise CustomerError("Phone is required")

    existing = _find_customer_by_phone(phone)

    # If exists → update fields
    if existing:
        update_fields = {}

        if payload.get("customer_name"):
            update_fields["customer_name"] = payload["customer_name"]

        if payload.get("email"):
            update_fields["custom_email"] = payload["email"]

        if payload.get("vat_number"):
            update_fields["custom_vat_registration_number"] = payload["vat_number"]

        if update_fields:
            erp_request(
                "PUT",
                f"/api/resource/Customer/{existing}",
                json=update_fields,
            )

        return existing
    print("PAYLOAD RECEIVED:", payload)
    # Create new customer
    customer_payload = {
        "doctype": "Customer",
        "customer_name": payload.get("customer_name") ,
        "customer_type": payload.get("customer_type") or "Individual",
        "customer_group": "Individual",
        "territory": "All Territories",
        "custom_phone_number": phone,
        "custom_email": payload.get("email"),
    }

    if payload.get("vat_number"):
        customer_payload["custom_vat_registration_number"] = payload["vat_number"]

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
