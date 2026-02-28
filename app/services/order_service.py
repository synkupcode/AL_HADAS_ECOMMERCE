from typing import Dict, Any, List
from datetime import datetime, timezone

from app.core.site_control import SiteControl
from app.integrations.erp_client import erp_request
from app.services.customer_service import get_or_create_customer
from app.services.ecommerce.ecommerce_engine import EcommerceEngine


class OrderValidationError(ValueError):
    pass


# -----------------------------------
# Helpers
# -----------------------------------

def _now_date():
    return datetime.now(timezone.utc).date().isoformat()


# IMPORTANT:
# Make sure this exists in your file
# (You already had this earlier)
def _resolve_checkout_price(item_code: str) -> float:
    item = erp_request(
        "GET",
        f"/api/resource/Item/{item_code}",
    ).get("data")

    if not item:
        raise OrderValidationError(f"Item not found: {item_code}")

    transformed = EcommerceEngine.transform_item(item)

    if not transformed["is_price_visible"]:
        raise OrderValidationError(f"Price is hidden for item {item_code}")

    price = transformed["price"]

    if price is None:
        raise OrderValidationError(f"No valid price available for {item_code}")

    return float(price)


# -----------------------------------
# RFQ Creator (Your Existing Logic)
# -----------------------------------

def create_ecommerce_rfq(payload: Dict[str, Any]) -> Dict[str, Any]:

    cart: List[Dict[str, Any]] = payload.get("cart", [])
    if not cart:
        raise OrderValidationError("Cart cannot be empty")

    customer_id = get_or_create_customer(payload)

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
            "quantity": qty,
            "unit_pricex": unit_price,
            "amount": amount,
        })

    rfq_payload = {
        "doctype": "E-Commerce RFQ",
        "customer_name": customer_id,
        "item_table": items_payload,
    }

    res = erp_request(
        "POST",
        "/api/resource/E-Commerce RFQ",
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


# -----------------------------------
# Sales Order Creator (ERP Standard)
# -----------------------------------

def create_sales_order(payload: Dict[str, Any]) -> Dict[str, Any]:

    cart: List[Dict[str, Any]] = payload.get("cart", [])
    if not cart:
        raise OrderValidationError("Cart cannot be empty")

    customer_id = get_or_create_customer(payload)

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
            "qty": qty,
            "rate": unit_price,
            "amount": amount,
        })

    sales_payload = {
        "doctype": "Sales Order",
        "customer": customer_id,
        "items": items_payload,
    }

    res = erp_request(
        "POST",
        "/api/resource/Sales Order",
        json=sales_payload,
    )

    doc = res.get("data") or {}
    order_id = doc.get("name")

    if not order_id:
        raise OrderValidationError("Sales Order creation failed")

    return {
        "status": "submitted",
        "sales_order_id": order_id,
        "customer_id": customer_id,
    }


# -----------------------------------
# Unified Dispatcher
# -----------------------------------

def create_ecommerce_order(payload: Dict[str, Any]) -> Dict[str, Any]:

    order_type = SiteControl.get_default_order_type()

    if order_type == "Sales Order":
        return create_sales_order(payload)

    return create_ecommerce_rfq(payload)
