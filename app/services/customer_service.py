from typing import Dict, Any
import logging
from app.integrations.erp_client import erp_request

logger = logging.getLogger(__name__)


class CustomerError(ValueError):
    pass


def _find_customer_by_phone(phone: str) -> str | None:
    res = erp_request(
        "GET",
        "/api/resource/Customer",
        params={
            "filters": f'[["mobile_no","=","{phone}"]]',
            "fields": '["name"]',
            "limit_page_length": 1,
        },
    )

    data = res.get("data") or []
    if data:
        return data[0]["name"]

    return None


def get_or_create_customer(payload: Dict[str, Any]) -> str:
    # 🔍 DEBUG LOGS
    logger.info("=== CUSTOMER PAYLOAD RECEIVED ===")
    logger.info("Full Payload: %s", payload)
    logger.info("Email Value: %s", repr(payload.get("email")))
    logger.info("=================================")

    phone = payload.get("phone")
    if not phone:
        raise CustomerError("Phone is required")

    existing = _find_customer_by_phone(phone)

    # Update existing customer
    if existing:
        update_fields = {}

        if payload.get("customer_name"):
            update_fields["customer_name"] = payload["customer_name"]

        if payload.get("email"):
            update_fields["custom_email"] = payload["email"]

        if payload.get("vat_number"):
            update_fields["custom_vat_registration_number"] = payload["vat_number"]

        if payload.get("company_name"):
            update_fields["company_name"] = payload["company_name"]

        if update_fields:
            logger.info("Updating Customer %s with: %s", existing, update_fields)

            erp_request(
                "PUT",
                f"/api/resource/Customer/{existing}",
                json=update_fields,
            )

        return existing

    # Create new customer
    customer_payload = {
        "doctype": "Customer",
        "customer_name": payload.get("customer_name") or phone,
        "customer_type": payload.get("customer_type") or "Individual",
        "customer_group": "Individual",
        "territory": "All Territories",
        "mobile_no": phone,
        "custom_email": payload.get("email"),
        "company_name": payload.get("company_name"),
        "custom_vat_registration_number": payload.get("vat_number"),
        "custom_cr_number": payload.get("cr_no"),
        "custom_customer_code": payload.get("customer_code"),
    }

    logger.info("Creating Customer with: %s", customer_payload)

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
