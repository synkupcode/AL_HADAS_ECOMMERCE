from typing import Dict, Any

from fastapi import HTTPException

from app.core.site_control import SiteControl
from app.integrations.erp_client import erp_request, ERPError


class CustomerError(ValueError):
    pass


# -------------------------------------------------
# Find Customer by Phone
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
# Get or Create Customer
# -------------------------------------------------
def get_or_create_customer(payload: Dict[str, Any]) -> str:

    # =================================================
    # 🔐 MASTER INTEGRATION SWITCH
    # =================================================
    if not SiteControl.is_website_integration_enabled():
        raise HTTPException(
            status_code=503,
            detail="E-commerce integration is currently disabled."
        )

    # =================================================
    # 🔐 CUSTOMER SYNC CONTROL
    # =================================================
    if not SiteControl.is_customer_sync_enabled():
        raise CustomerError("Customer creation is disabled.")

    phone = payload.get("phone")
    if not phone:
        raise CustomerError("Phone is required.")

    # -------------------------------------------------
    # Check Existing Customer
    # -------------------------------------------------
    existing = _find_customer_by_phone(phone)

    # =================================================
    # UPDATE EXISTING CUSTOMER
    # =================================================
    if existing:
        update_fields = {}

        if payload.get("customer_name"):
            update_fields["customer_name"] = payload["customer_name"]

        email_value = payload.get("email")
        if email_value and str(email_value).strip():
            update_fields["custom_email"] = str(email_value).strip()

        if payload.get("vat_number"):
            update_fields["custom_vat_registration_number"] = payload["vat_number"]

        if update_fields:
            try:
                erp_request(
                    "PUT",
                    f"/api/resource/Customer/{existing}",
                    json=update_fields,
                )
            except ERPError:
                raise CustomerError("Customer update temporarily unavailable.")

        return existing

    # =================================================
    # CREATE NEW CUSTOMER
    # =================================================
    email_value = payload.get("email")
    if email_value:
        email_value = str(email_value).strip()

    customer_payload = {
        "doctype": "Customer",
        "customer_name": payload.get("customer_name") or phone,
        "customer_type": payload.get("customer_type") or "Individual",
        "customer_group": "Individual",
        "territory": "All Territories",
        "custom_phone_number": phone,
        "custom_email": email_value if email_value else None,
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
