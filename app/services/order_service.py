from datetime import datetime, timezone
from typing import Dict, Any, List, Tuple, Optional

from app.core.config import settings
from app.integrations.erp_client import erp_request
from app.services.customer_service import get_or_create_customer
from app.services.ecommerce.ecommerce_engine import EcommerceEngine


class OrderValidationError(ValueError):
    pass


def _now_date():
    return datetime.now(timezone.utc).date().isoformat()


# -------------------------------------------------
# Fetch Item From ERP
# -------------------------------------------------
def _fetch_item_from_erp(item_code: str) -> Dict[str, Any]:

    fields = [
        "item_code",
        "item_name",
        "custom_standard_selling_price",
        "custom_ecommerce_price",
        "custom_mrp_price",
        "custom_fixed_price",
        "custom_mrp_rate",
        "custom_enable_promotion",
        "custom_promotion_base_price",
        "custom_promotion_type",
        "custom_promotion_discount_",
        "custom_promotion_start",
        "custom_promotion_end",
        "custom_promotion_price_manual",
        "custom_promotional_price",
        "custom_promotional_rate",
        "custom_show_price",
    ]

    res = erp_request(
        "GET",
        f"/api/resource/Item/{item_code}",
        params={"fields": str(fields).replace("'", '"')},
    )

    item = res.get("data")
    if not item:
        raise OrderValidationError(f"Item not found: {item_code}")

    return item


# -------------------------------------------------
# Fetch Customer Contact From ERP
# -------------------------------------------------
def _get_customer_contact_details(customer_id: str) -> Tuple[Optional[str], Optional[str]]:

    res = erp_request(
        "GET",
        "/api/resource/Contact",
        params={
            "filters": f'[["links.link_doctype","=","Customer"],["links.link_name","=","{customer_id}"]]',
            "fields": '["email_ids","phone_nos"]',
            "limit_page_length": 1,
        },
    )

    data = res.get("data") or []

    if not data:
        return None, None

    contact = data[0]

    email = None
    mobile = None

    email_ids = contact.get("email_ids") or []
    phone_nos = contact.get("phone_nos") or []

    if email_ids:
        email = email_ids[0].get("email_id")

    if phone_nos:
        mobile = phone_nos[0].get("phone")

    return email, mobile


# -------------------------------------------------
# Resolve Checkout Price
# -------------------------------------------------
def _resolve_checkout_price(item_code: str) -> float:

    item = _fetch_item_from_erp(item_code)

    transformed = EcommerceEngine.transform_item(item)

    if not transformed["is_price_visible"]:
        raise OrderValidationError(f"Price is hidden for item {item_code}")

    price = transformed["price"]

    if price is None:
        raise OrderValidationError(f"No valid price available for item {item_code}")

    return float(price)


# -------------------------------------------------
# Create Ecommerce RFQ
# -------------------------------------------------
def create_ecommerce_rfq(payload: Dict[str, Any]) -> Dict[str, Any]:

    cart: List[Dict[str, Any]] = payload.get("cart", [])
    if not cart:
        raise OrderValidationError("Cart cannot be empty")

    # Customer (VAT-based, idempotent)
    customer_id = get_or_create_customer(payload)

    # 🔥 Fetch email & mobile from ERP Contact
    email, mobile = _get_customer_contact_details(customer_id)

    items_payload = []

    for item in cart:

        item_code = item.get("item_code")
        if not item_code:
            raise OrderValidationError("Item code required")

        qty = float(item.get("qty", 0))
        if qty <= 0:
            raise OrderValidationError("Quantity must be greater than zero")

        unit_price = _resolve_checkout_price(item_code)

        amount = qty * unit_price

        items_payload.append({
            "item_code": item_code,
            "item_name": item.get("item_name"),
            "quantity": qty,
            "unit_pricex": unit_price,
            "uom": item.get("uom"),
            "amount": amount,
        })

    # RFQ Payload
    rfq_payload = {
        "doctype": settings.ECOM_RFQ_DOCTYPE,
        "customer_name": customer_id,

        # Backend-driven contact data
        "email_id": email,
        "mobile_no": mobile,

        "building_no": payload.get("address", {}).get("building_no"),
        "postal_code": payload.get("address", {}).get("postal_code"),
        "street_name": payload.get("address", {}).get("street_name"),
        "district": payload.get("address", {}).get("district"),
        "city": payload.get("address", {}).get("city"),
        "country": payload.get("address", {}).get("country"),
        "full_address": payload.get("address", {}).get("full_address"),

        "item_table": items_payload,
    }

    # Clean empty values (safe cleanup)
    rfq_payload = {
        k: v for k, v in rfq_payload.items()
        if v not in (None, "", [])
    }

    res = erp_request(
        "POST",
        f"/api/resource/{settings.ECOM_RFQ_DOCTYPE}",
        json=rfq_payload,
    )

    doc = res.get("data") or {}
    rfq_id = doc.get("name")

    if not rfq_id:
        raise OrderValidationError("RFQ creation failed")

    return {
        "status": "submitted",
        "ecommerce_rfq_id": rfq_id,
        "customer_id": customer_id,
        "created_at": _now_date(),
    }
