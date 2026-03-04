from typing import Dict, Any

from fastapi import HTTPException

from app.core.site_control import SiteControl
from app.integrations.erp_client import erp_request, ERPError


class CustomerError(ValueError):
    pass


# -------------------------------------------------
# Find Customer by Phone (Legacy Support)
# -------------------------------------------------
def _find_customer_by_phone(phone: str) -> str | None:
    try:
        res = erp_request(
            "GET",
            "/api/resource/Customer",
            params={
                "filters": f'[["custom_phone_number","=","{phone}"]]',
                "fields": '["name"]',
                "limit_page_length": 1,
            },
        )
    except ERPError:
        raise CustomerError("Customer service temporarily unavailable.")

    data = res.get("data") or []

    if data:
        return data[0]["name"]

    return None


# -------------------------------------------------
# Find Customer by Email (Primary Identity)
# -------------------------------------------------
def find_customer_by_email(email: str) -> Dict[str, Any] | None:
    try:
        res = erp_request(
            "GET",
            "/api/resource/Customer",
            params={
                "filters": f'[["custom_email","=","{email}"]]',
                "fields": '["name","customer_name","custom_phone_number","custom_email","custom_vat_registration_number"]',
                "limit_page_length": 1,
            },
        )
    except ERPError:
        raise CustomerError("Customer lookup temporarily unavailable.")

    data = res.get("data") or []

    if len(data) > 1:
        raise CustomerError("Multiple customers found with same email. Contact support.")

    if data:
        return data[0]

    return None


# -------------------------------------------------
# Get or Create Customer (SAFE UPSERT)
# -------------------------------------------------
def get_or_create_customer(payload: Dict[str, Any]) -> str:

    # 🔐 Master Integration Switch
    if not SiteControl.is_website_integration_enabled():
        raise HTTPException(
            status_code=503,
            detail="E-commerce integration is currently disabled."
        )

    # 🔐 Customer Sync Control
    if not SiteControl.is_customer_sync_enabled():
        raise CustomerError("Customer creation is disabled.")

    email = payload.get("email")
    phone = payload.get("phone")

    if not email and not phone:
        raise CustomerError("Email or Phone is required.")

    # -------------------------------------------------
    # 1️⃣ Try Find by Email (Primary)
    # -------------------------------------------------
    if email:
        existing = find_customer_by_email(email)
        if existing:
            return existing["name"]

    # -------------------------------------------------
    # 2️⃣ Fallback: Find by Phone (Backward Compatibility)
    # -------------------------------------------------
    if phone:
        existing_phone = _find_customer_by_phone(phone)
        if existing_phone:
            return existing_phone

    # -------------------------------------------------
    # 3️⃣ Create New Customer
    # -------------------------------------------------
    email_value = str(email).strip() if email else None
    phone_value = str(phone).strip() if phone else None

    customer_payload = {
        "doctype": "Customer",
        "customer_name": payload.get("customer_name") or phone_value or email_value,
        "customer_type": payload.get("customer_type") or "Individual",
        "customer_group": "Individual",
        "territory": "All Territories",
        "custom_phone_number": phone_value,
        "custom_email": email_value,
    }

    if payload.get("vat_number"):
        customer_payload["custom_vat_registration_number"] = payload["vat_number"]

    try:
        res = erp_request(
            "POST",
            "/api/resource/Customer",
            json=customer_payload,
        )
    except ERPError:
        raise CustomerError("Customer creation temporarily unavailable.")

    doc = res.get("data") or {}
    customer_id = doc.get("name")

    if not customer_id:
        raise CustomerError("Customer creation failed.")

    return customer_id
