from typing import Dict, Any, List

from app.core.site_control import SiteControl
from app.integrations.erp_client import erp_request
from app.services.customer_service import get_or_create_customer
from app.services.ecommerce.ecommerce_engine import EcommerceEngine


class OrderValidationError(ValueError):
    pass


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

        if unit_price is None:
            raise OrderValidationError(f"Price not available for {item_code}")

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
# Unified Order Dispatcher
# -----------------------------------
def create_ecommerce_order(payload: Dict[str, Any]) -> Dict[str, Any]:

    order_type = SiteControl.get_default_order_type()

    if order_type == "Sales Order":
        return create_sales_order(payload)

    return create_ecommerce_rfq(payload)
