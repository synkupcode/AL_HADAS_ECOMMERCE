from datetime import datetime, timezone
from typing import Dict, Any, List

from fastapi import HTTPException

from app.core.site_control import SiteControl
from app.core.config import settings
from app.integrations.erp_client import erp_request, ERPError
from app.services.customer_service import get_or_create_customer
from app.services.ecommerce.ecommerce_engine import EcommerceEngine


class OrderValidationError(ValueError):
    pass


def _today():
    return datetime.now(timezone.utc).date().isoformat()


# =================================================
# FETCH ITEM FROM ERP (USED FOR PRICING)
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

    try:
        res = erp_request(
            method="GET",
            path=f"/api/resource/Item/{item_code}",
            params={"fields": str(fields).replace("'", '"')},
        )
    except ERPError:
        raise OrderValidationError("Item service temporarily unavailable.")

    item = res.get("data")
    if not item:
        raise OrderValidationError(f"Item not found: {item_code}")

    return item


# =================================================
# RFQ
# =================================================
def create_ecommerce_rfq(payload: Dict[str, Any]) -> Dict[str, Any]:

    # 🔐 MASTER SWITCH
    if not SiteControl.is_website_integration_enabled():
        raise HTTPException(
            status_code=503,
            detail="E-commerce integration is currently disabled."
        )

    # 🔐 CUSTOMER CONTROL
    if not SiteControl.is_customer_sync_enabled():
        raise OrderValidationError("Customer service is disabled.")

    # 🔐 MAINTENANCE CHECK
    if SiteControl.is_site_frozen():
        raise OrderValidationError("Store is currently under maintenance.")

    cart: List[Dict[str, Any]] = payload.get("cart", [])
    if not cart:
        raise OrderValidationError("Cart cannot be empty")

    customer_id = get_or_create_customer(payload)
    items_payload = []

    for item in cart:
        item_code = item.get("item_code")
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

    rfq_payload = {
        "doctype": settings.ECOM_RFQ_DOCTYPE,
        "customer_name": customer_id,
        "item_table": items_payload,
    }

    try:
        res = erp_request(
            method="POST",
            path=f"/api/resource/{settings.ECOM_RFQ_DOCTYPE}",
            json=rfq_payload,
        )
    except ERPError:
        raise OrderValidationError("Order service temporarily unavailable.")

    doc = res.get("data") or {}
    rfq_id = doc.get("name")

    return {
        "status": "submitted",
        "ecommerce_rfq_id": rfq_id,
        "customer_id": customer_id,
        "created_at": _today(),
    }


# =================================================
# SALES ORDER
# =================================================
def create_sales_order(payload: Dict[str, Any]) -> Dict[str, Any]:

    # 🔐 MASTER SWITCH
    if not SiteControl.is_website_integration_enabled():
        raise HTTPException(
            status_code=503,
            detail="E-commerce integration is currently disabled."
        )

    # 🔐 CUSTOMER CONTROL
    if not SiteControl.is_customer_sync_enabled():
        raise OrderValidationError("Customer service is disabled.")

    # 🔐 MAINTENANCE CHECK
    if SiteControl.is_site_frozen():
        raise OrderValidationError("Store is currently under maintenance.")

    cart: List[Dict[str, Any]] = payload.get("cart", [])
    if not cart:
        raise OrderValidationError("Cart cannot be empty")

    customer_id = get_or_create_customer(payload)
    address = payload.get("address", {})

    DEFAULT_WAREHOUSE = SiteControl.get_default_source_warehouse()
    if not DEFAULT_WAREHOUSE:
        raise OrderValidationError("Default warehouse not configured.")

    items_payload = []

    for item in cart:
        item_code = item.get("item_code")
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
            "qty": qty,
            "uom": item.get("uom"),
            "price_list_rate": unit_price,
            "rate": unit_price,
            "amount": qty * unit_price,
            "warehouse": DEFAULT_WAREHOUSE,
        })

    sales_order_payload = {
        "doctype": "Sales Order",
        "customer": customer_id,
        "transaction_date": _today(),
        "delivery_date": _today(),
        "set_warehouse": DEFAULT_WAREHOUSE,
        "selling_price_list": "Standard Selling",
        "items": items_payload,
        "address_display": address.get("full_address"),
    }

    try:
        res = erp_request(
            method="POST",
            path="/api/resource/Sales Order",
            json=sales_order_payload,
        )
    except ERPError:
        raise OrderValidationError("Order service temporarily unavailable.")

    doc = res.get("data") or {}
    so_id = doc.get("name")

    return {
        "status": "submitted",
        "ecommerce_rfq_id": so_id,
        "customer_id": customer_id,
        "created_at": _today(),
    }


# =================================================
# ENTRY POINT
# =================================================
def create_ecommerce_order(payload: Dict[str, Any]) -> Dict[str, Any]:

    order_type = SiteControl.get_default_order_type()

    if order_type == "E-Commerce RFQ":
        return create_ecommerce_rfq(payload)

    elif order_type == "Sales Order":
        return create_sales_order(payload)

    else:
        raise OrderValidationError("Invalid Default Order Type.")
