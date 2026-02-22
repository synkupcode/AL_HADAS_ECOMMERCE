from datetime import datetime, timezone
from typing import Dict, Any, List

from app.core.config import settings
from app.integrations.erp_client import erp_request
from app.services.customer_service import get_or_create_customer


MAX_QTY_PER_ITEM = 1000


class OrderValidationError(ValueError):
    pass


def _now_date():
    return datetime.now(timezone.utc).date().isoformat()


def create_ecommerce_rfq(payload: Dict[str, Any]) -> Dict[str, Any]:

    # -------------------------
    # VALIDATION
    # -------------------------

    cart: List[Dict[str, Any]] = payload.get("cart", [])
    if not cart:
        raise OrderValidationError("Cart cannot be empty")

    if not payload.get("customer_name"):
        raise OrderValidationError("Customer name is required")

    if not payload.get("phone"):
        raise OrderValidationError("Phone number is required")

    address = payload.get("address") or {}

    required_address_fields = [
        "address_line1",
        "postal_code",
        "city",
        "country",
    ]

    for field in required_address_fields:
        if not address.get(field):
            raise OrderValidationError(f"{field} is required")

    # -------------------------
    # CUSTOMER (AUTO-NUMBER SAFE)
    # -------------------------

    customer_id = get_or_create_customer(payload)

    # -------------------------
    # PREPARE ITEMS
    # -------------------------

    preview_items = []

    for item in cart:
        if not item.get("item_code") or not item.get("qty"):
            raise OrderValidationError("Invalid cart item")

        qty = float(item["qty"])

        if qty <= 0:
            raise OrderValidationError("Quantity must be greater than zero")

        if qty > MAX_QTY_PER_ITEM:
            raise OrderValidationError("Quantity exceeds allowed limit")

        preview_items.append({
            "item_code": item["item_code"],
            "quantity": qty  # Must match ERP child table field
        })

    # -------------------------
    # BUILD ERP PAYLOAD
    # -------------------------

    rfq_payload = {
        "doctype": settings.ECOM_RFQ_DOCTYPE,

        # Proper ERP link
        "customer": customer_id,

        # Snapshot fields
        "customer_name": payload.get("customer_name"),
        "email_id": payload.get("contact", {}).get("email"),
        "company_name": payload.get("company_name"),
        "phone_number": payload.get("phone"),
        "cr_no": payload.get("cr_no"),
        "vat_id": payload.get("vat_number"),

        "address_line1": address.get("address_line1"),
        "postal_code": address.get("postal_code"),
        "city": address.get("city"),
        "country": address.get("country"),

        # Child table
        settings.ECOM_RFQ_ITEM_TABLE_FIELD: preview_items,

        "transaction_date": _now_date(),
        "notes": payload.get("notes", "")
    }

    rfq_payload = {k: v for k, v in rfq_payload.items() if v is not None}

    # -------------------------
    # CREATE RFQ IN ERP
    # -------------------------

    res = erp_request(
        "POST",
        f"/api/resource/{settings.ECOM_RFQ_DOCTYPE_URL}",
        json=rfq_payload,
    )

    doc = res.get("data") or {}
    rfq_id = doc.get("name")

    if not rfq_id:
        raise OrderValidationError("E-Commerce RFQ creation failed")

    # -------------------------
    # RESPONSE
    # -------------------------

    return {
        "status": "submitted",
        "ecommerce_rfq_id": rfq_id,
        "customer_id": customer_id,
        "created_at": _now_date()
    }
