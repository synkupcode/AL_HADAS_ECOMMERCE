from datetime import datetime, timezone
from typing import Dict, Any, List

from app.core.site_control import SiteControl
from app.core.config import settings
from app.integrations.erp_client import erp_request
from app.services.customer_service import get_or_create_customer
from app.services.ecommerce.ecommerce_engine import EcommerceEngine


# -------------------------------------------------
# Custom Exception
# -------------------------------------------------
class OrderValidationError(ValueError):
    pass


# -------------------------------------------------
# Utility
# -------------------------------------------------
def _today():
    return datetime.now(timezone.utc).date().isoformat()


# =================================================
# FETCH ITEM (USED FOR RFQ)
# =================================================
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
        method="GET",
        path=f"/api/resource/Item/{item_code}",
        params={"fields": str(fields).replace("'", '"')},
    )

    item = res.get("data")
    if not item:
        raise OrderValidationError(f"Item not found: {item_code}")

    return item


# =================================================
# EXISTING RFQ FLOW (UNCHANGED LOGIC)
# =================================================
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

        item_data = _fetch_item_from_erp(item_code)
        transformed = EcommerceEngine.transform_item(item_data)

        if not transformed["is_price_visible"]:
            raise OrderValidationError(f"Price hidden for item {item_code}")

        unit_price = transformed["price"]

        items_payload.append({
            "item_code": item_code,
            "item_name": item.get("item_name"),
            "quantity": qty,
            "unit_pricex": unit_price,
            "uom": item.get("uom"),
            "amount": qty * unit_price,
        })

    # ADDRESS (MANDATORY FOR YOUR ERP RFQ)
    address = payload.get("address", {})

    rfq_payload = {
        "doctype": settings.ECOM_RFQ_DOCTYPE,
        "customer_name": customer_id,
        "building_no": address.get("building_no"),
        "postal_code": address.get("postal_code"),
        "city": address.get("city"),
        "full_address": address.get("full_address"),
        "item_table": items_payload,
    }

    rfq_payload = {
        k: v for k, v in rfq_payload.items()
        if v not in (None, "", [])
    }

    res = erp_request(
        method="POST",
        path=f"/api/resource/{settings.ECOM_RFQ_DOCTYPE}",
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


# =================================================
# NEW — SALES ORDER (DRAFT)
# =================================================
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
        "transaction_date": _today(),
        "delivery_date": _today(),  # FIXED: Required by your ERP
        "items": items_payload,
    }

    res = erp_request(
        method="POST",
        path="/api/resource/Sales Order",
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


# =================================================
# UNIFIED ENTRY POINT
# =================================================
def create_ecommerce_order(payload: Dict[str, Any]) -> Dict[str, Any]:

    order_type = SiteControl.get_default_order_type()

    if order_type == "E-Commerce RFQ":
        return create_ecommerce_rfq(payload)

    elif order_type == "Sales Order":
        return create_sales_order(payload)

    else:
        raise OrderValidationError("Invalid Default Order Type in Settings")
