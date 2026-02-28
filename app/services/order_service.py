from datetime import datetime, timezone
from typing import Dict, Any, List

from app.core.site_control import SiteControl
from app.core.config import settings
from app.integrations.erp_client import erp_request
from app.services.customer_service import get_or_create_customer
from app.services.ecommerce.ecommerce_engine import EcommerceEngine


class OrderValidationError(ValueError):
    pass


def _today():
    return datetime.now(timezone.utc).date().isoformat()


# -------------------------------------------------
# EXISTING FUNCTION (UNCHANGED)
# -------------------------------------------------
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

        unit_price = EcommerceEngine.transform_item(
            _fetch_item_from_erp(item_code)
        )["price"]

        items_payload.append({
            "item_code": item_code,
            "item_name": item.get("item_name"),
            "quantity": qty,
            "unit_pricex": unit_price,
            "uom": item.get("uom"),
            "amount": qty * unit_price,
        })

    rfq_payload = {
        "doctype": settings.ECOM_RFQ_DOCTYPE,
        "customer_name": customer_id,
        "item_table": items_payload,
    }

    rfq_payload = {k: v for k, v in rfq_payload.items() if v not in (None, "", [])}

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
        "created_at": _today(),
    }


# -------------------------------------------------
# NEW — SALES ORDER (DRAFT)
# -------------------------------------------------
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

        items_payload.append({
            "item_code": item_code,
            "qty": qty,
            "rate": float(item.get("unit_price", 0)),
        })

    sales_order_payload = {
        "doctype": "Sales Order",
        "customer": customer_id,
        "transaction_date": _today(),  # safe default
        "items": items_payload,
    }

    res = erp_request(
        "POST",
        "/api/resource/Sales Order",
        json=sales_order_payload,
    )

    doc = res.get("data") or {}
    so_id = doc.get("name")

    if not so_id:
        raise OrderValidationError("Sales Order creation failed")

    return {
        "status": "draft",
        "sales_order_id": so_id,
        "customer_id": customer_id,
    }


# -------------------------------------------------
# UNIFIED ENTRY POINT (NEW)
# -------------------------------------------------
def create_ecommerce_order(payload: Dict[str, Any]) -> Dict[str, Any]:

    order_type = SiteControl.get_default_order_type()

    if order_type == "E-Commerce RFQ":
        return create_ecommerce_rfq(payload)

    elif order_type == "Sales Order":
        return create_sales_order(payload)

    else:
        raise OrderValidationError("Invalid Default Order Type in Settings")
