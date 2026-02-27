from typing import Dict, Any
from app.integrations.erp_client import erp_request


class CustomerError(ValueError):
    pass


ALLOWED_CUSTOMER_TYPES = {"Individual", "Company", "Partnership"}


def _normalize_customer_type(value: str | None) -> str:
    if not value:
        return "Individual"

    value = value.strip().title()

    if value not in ALLOWED_CUSTOMER_TYPES:
        return "Individual"

    return value


def _normalize_vat(vat: str) -> str:
    return vat.strip().replace(" ", "").upper()


def _find_customer_by_vat(vat_number: str) -> str | None:
    res = erp_request(
        "GET",
        "/api/resource/Customer",
        params={
            "filters": f'[["custom_vat_registration_number","=","{vat_number}"]]',
            "fields": '["name"]',
            "limit_page_length": 1,
        },
    )

    data = res.get("data") or []
    if data:
        return data[0].get("name")

    return None


def create_customer(payload: Dict[str, Any]) -> str:
    customer_name = payload.get("customer_name")
    vat_number = payload.get("vat_number")

    if not customer_name:
        raise CustomerError("Customer name is required")

    if not vat_number:
        raise CustomerError("VAT number is required")

    vat_number = _normalize_vat(vat_number)

    customer_payload = {
        "doctype": "Customer",
        "customer_name": customer_name,
        "customer_type": _normalize_customer_type(payload.get("customer_type")),
        "customer_group": payload.get("customer_group") or "Individual",
        "territory": payload.get("territory") or "All Territories",
        "custom_vat_registration_number": vat_number,

        # ✅ Your actual ERP fields
        "custom_email": payload.get("email"),
        "custom_phone_number": payload.get("phone"),
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
    customer_name = payload.get("customer_name")
    vat_number = payload.get("vat_number")

    if not customer_name:
        raise CustomerError("Customer name is required")

    if not vat_number:
        raise CustomerError("VAT number is required")

    vat_number = _normalize_vat(vat_number)

    existing = _find_customer_by_vat(vat_number)
    if existing:
        return existing

    return create_customer(payload)
