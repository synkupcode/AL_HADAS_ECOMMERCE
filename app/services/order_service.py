from datetime import datetime, timezone
from typing import Dict, Any, List

from app.core.config import settings
from app.integrations.erp_client import erp_request
from app.services.customer_service import get_or_create_customer


class OrderValidationError(ValueError):
    pass


def _now_date():
    return datetime.now(timezone.utc).date().isoformat()


def create_ecommerce_rfq(payload: Dict[str, Any]) -> Dict[str, Any]:

    # -------------------------
    # BASIC VALIDATION
    # -------------------------

    cart: List[Dict[str, Any]] = payload.get("cart", [])
    if not cart:
        raise OrderValidationError("Cart cannot be empty")

    if not payload.get("customer_name"):
        raise OrderValidationError("Customer name is required")

    if not payload.get("phone"):
        raise OrderValidationError("Phone number is required")

    address = payload.get("address") or {}
    contact = payload.get("contact") or {}

    required_address_fields = [
        "building_no",
        "postal_code",
        "street_name",
        "city",
        "country",
        "full_address"
    ]

    for field in required_address_fields:
        if not address.get(field):
            raise OrderValidationError(f"{field} is required")

    # -------------------------
    # ENSURE CUSTOMER EXISTS
    # -------------------------

    customer_id = get_or_create_customer(payload)

    # -------------------------
    # PREPARE CHILD TABLE ITEMS
    # -------------------------

    items_payload = []

    for item in cart:

        if not item.get("item_code"):
            raise OrderValidationError("Item code is required")

        if not item.get("qty"):
            raise OrderValidationError("Quantity is required")

        qty = float(item["qty"])
        if qty <= 0:
            raise OrderValidationError("Quantity must be greater than zero")

        unit_price = float(item.get("unit_price", 0))
        amount = qty * unit_price

        items_payload.append({
            "item_code": item["item_code"],
            "item_name": item.get("item_name"),
            "quantity": qty,
            "unit_pricex": unit_price,
            "uom": item.get("uom"),
            "amount": amount,
        })

    # -------------------------
    # BUILD RFQ PAYLOAD
    # -------------------------

    rfq_payload = {
        "doctype": settings.ECOM_RFQ_DOCTYPE,

        # Customer Information
        "customer_name": payload.get("customer_name"),
        "email_id": contact.get("email"),
        "company_name": payload.get("company_name"),
        "phone_number": payload.get("phone"),
        "cr_no": payload.get("cr_no"),
        "vat_id": payload.get("vat_number"),

        # Address Information
        "building_no": address.get("building_no"),
        "postal_code": address.get("postal_code"),
        "street_name": address.get("street_name"),
        "district": address.get("district"),
        "city": address.get("city"),
        "country": address.get("country"),
        "full_address": address.get("full_address"),

        # Child Table
        "item_table": items_payload,
    }

    # Remove empty values
    rfq_payload = {
        k: v for k, v in rfq_payload.items()
        if v not in (None, "", [])
    }

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
        "created_at": _now_date(),
    }
