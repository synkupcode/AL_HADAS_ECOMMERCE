from typing import Dict, Any
from app.integrations.erp_client import erp_request
import logging

logger = logging.getLogger(__name__)


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

    # 🔍 ALWAYS LOG PAYLOAD
    logger.info("=== CUSTOMER PAYLOAD RECEIVED ===")
    logger.info("Full Payload: %s", payload)
    logger.info("Email Value: %s", repr(payload.get("email")))
    logger.info("=================================")

    phone = payload.get("phone")
    if not phone:
        raise CustomerError("Phone is required")

    existing = _find_customer_by_phone(phone)

    # -------------------------
    # UPDATE EXISTING CUSTOMER
    # -------------------------
    if existing:
        update_fields = {}

        if payload.get("customer_name"):
            update_fields["customer_name"] = payload["customer_name"]

        # 🔥 EMAIL UPDATE (IMPORTANT)
        if payload.get("email"):
            update_fields["custom_email"] = payload["email"]

        if payload.get("vat_number"):
            update_fields["custom_vat_registration_number"] = payload["vat_number"]

        if update_fields:
            logger.info("Updating Customer %s with: %s", existing, update_fields)

            erp_request(
                "PUT",
                f"/api/resource/Customer/{existing}",
                json=update_fields,
            )

        return existing

    # -------------------------
    # CREATE NEW CUSTOMER
    # -------------------------

    logger.info("Creating new customer...")

    customer_payload = {
        "doctype": "Customer",
        "customer_name": payload.get("customer_name") or phone,
        "customer_type": payload.get("customer_type") or "Individual",
        "customer_group": "Individual",
        "territory": "All Territories",
        "mobile_no": phone,

        # 🔥 EMAIL FIELD (MUST MATCH YOUR ERP FIELD NAME)
        "custom_email": payload.get("email"),
    }

    if payload.get("vat_number"):
        customer_payload["custom_vat_registration_number"] = payload["vat_number"]

    logger.info("Customer Create Payload: %s", customer_payload)

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
