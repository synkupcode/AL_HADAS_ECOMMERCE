from datetime import datetime, timezone
from typing import Dict, Any, List

from app.core.config import settings
from app.integrations.erp_client import erp_request
from app.services.customer_service import get_or_create_customer


class OrderValidationError(ValueError):
    pass


def _now_date():
    return datetime.now(timezone.utc).date().isoformat()


def _get_item_price(item_code: str) -> float:
    """
    STRICT: Fetch price from ERP.
    Adjust price list logic as needed.
    """

    res = erp_request(
        "GET",
        "/api/resource/Item Price",
        params={
            "filters": f'[["item_code","=","{item_code}"]]',
            "fields": '["price_list_rate"]'
        },
    )

    data = res.get("data") or []
    if not data:
        raise OrderValidationError(f"No price found for item {item_code}")

    return float(data[0]["price_list_rate"])


def create_ecommerce_rfq(payload: Dict[str, Any]) -> Dict[str, Any]:

    cart: List[Dict[str, Any]] = payload.get("cart", [])
    if not cart:
        raise OrderValidationError("Cart cannot be empty")

    # Ensure customer exists
    customer_id = get_or_create_customer(payload)

    items_payload = []

    for item in cart:

        if not item.get("item_code"):
            raise OrderValidationError("Item code required")

        if not item.get("qty"):
            raise OrderValidationError("Quantity required")

        qty = float(item["qty"])
        if qty <= 0:
            raise OrderValidationError("Quantity must be greater than zero")

        # STRICT ERP PRICE
        unit_price = _get_item_price(item["item_code"])
        amount = qty * unit_price

        items_payload.append({
            "item_code": item["item_code"],
            "item_name": item.get("item_name"),
            "quantity": qty,
            "unit_pricex": unit_price,
            "uom": item.get("uom"),
            "amount": amount,
        })

    rfq_payload = {
        "doctype": settings.ECOM_RFQ_DOCTYPE,

        # Proper Link to Customer
        "customer_name": customer_id,

        "email_id": payload.get("contact", {}).get("email"),
        "phone_number": payload.get("phone"),

        "building_no": payload.get("address", {}).get("building_no"),
        "postal_code": payload.get("address", {}).get("postal_code"),
        "street_name": payload.get("address", {}).get("street_name"),
        "district": payload.get("address", {}).get("district"),
        "city": payload.get("address", {}).get("city"),
        "country": payload.get("address", {}).get("country"),
        "full_address": payload.get("address", {}).get("full_address"),

        "item_table": items_payload,
    }

    rfq_payload = {k: v for k, v in rfq_payload.items() if v not in (None, "", [])}

    res = erp_request(
        "POST",
        f"/api/resource/{settings.ECOM_RFQ_DOCTYPE_URL}",
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
