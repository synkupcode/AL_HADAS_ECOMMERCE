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

    # ==============================
    # DEBUG PRINTS (VISIBLE IN RENDER)
    # ==============================
    print("========== CUSTOMER DEBUG ==========")
    print("FULL PAYLOAD:", payload)
    print("PAYLOAD KEYS:", list(payload.keys()))
    print("EMAIL VALUE:", payload.get("email"))
    print("====================================")

    phone = payload.get("phone")
    if not phone:
        raise CustomerError("Phone is required")

    existing = _find_customer_by_phone(phone)

    # ==================================================
    # UPDATE EXISTING CUSTOMER
    # ==================================================
    if existing:
        update_fields = {}

        if payload.get("customer_name"):
            update_fields["customer_name"] = payload["customer_name"]

        email_value = payload.get("email")
        if email_value and str(email_value).strip():
            update_fields["custom_email"] = str(email_value).strip()

        if payload.get("vat_number"):
            update_fields["custom_vat_registration_number"] = payload["vat_number"]

        print("UPDATE FIELDS:", update_fields)

        if update_fields:
            erp_request(
                "PUT",
                f"/api/resource/Customer/{existing}",
                json=update_fields,
            )

        return existing

    # ==================================================
    # CREATE NEW CUSTOMER
    # ==================================================
    print("Creating NEW customer...")

    email_value = payload.get("email")
    if email_value:
        email_value = str(email_value).strip()

    customer_payload = {
        "doctype": "Customer",
        "customer_name": payload.get("customer_name") or phone,
        "customer_type": payload.get("customer_type") or "Individual",
        "customer_group": "Individual",
        "territory": "All Territories",

        # Correct ERP fields
        "custom_phone_number": phone,
        "custom_email": email_value if email_value else None,
    }

    if payload.get("vat_number"):
        customer_payload["custom_vat_registration_number"] = payload["vat_number"]

    print("CUSTOMER CREATE PAYLOAD:", customer_payload)

    res = erp_request(
        "POST",
        "/api/resource/Customer",
        json=customer_payload,
    )

    print("ERP CREATE RESPONSE:", res)

    doc = res.get("data") or {}
    customer_id = doc.get("name")

    if not customer_id:
        raise CustomerError("Customer creation failed")

    return customer_id
