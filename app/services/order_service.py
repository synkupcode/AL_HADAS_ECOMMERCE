# app/services/order_service.py

from datetime import datetime, timezone
from typing import Dict, Any, List

from fastapi import HTTPException

from app.core.site_control import SiteControl
from app.core.config import settings
from app.integrations.erp_client import erp_request, ERPError
from app.services.customer_service import get_or_create_customer
from app.services.ecommerce.ecommerce_engine import EcommerceEngine
from app.services.stock_service import StockService


class OrderValidationError(ValueError):
    """Custom exception for order validation failures."""
    pass


def _today() -> str:
    """Return current UTC date in ISO format."""
    return datetime.now(timezone.utc).date().isoformat()


def _fetch_item_from_erp(item_code: str) -> Dict[str, Any]:
    """Fetch item details from ERPNext with required fields for pricing."""
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
        "custom_show_stock",
    ]

    try:
        res = erp_request(
            method="GET",
            path=f"/api/resource/Item/{item_code}",
            params={"fields": str(fields).replace("'", '"')}
        )
    except ERPError:
        raise OrderValidationError("Item service temporarily unavailable.")

    item = res.get("data")
    if not item:
        raise OrderValidationError(f"Item not found: {item_code}")
    return item


def _validate_address(address: Dict[str, Any]) -> None:
    """Ensure required address fields are present."""
    required_fields = ["building_no", "postal_code", "city", "full_address"]
    for field in required_fields:
        if not address.get(field):
            raise OrderValidationError(f"{field} is required")


def _prepare_items_payload(cart: List[Dict[str, Any]], warehouse: str = None) -> List[Dict[str, Any]]:
    """Transform cart items for ERPNext payload."""
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

        item_payload = {
            "item_code": item_code,
            "qty": qty,
            "uom": item.get("uom"),
            "rate": transformed["price"],
        }
        if warehouse:
            item_payload["warehouse"] = warehouse

        items_payload.append(item_payload)

    return items_payload


def create_ecommerce_rfq(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create an E-Commerce RFQ in ERPNext.
    Reserves stock during processing and releases it finally.
    """
    if not SiteControl.is_website_integration_enabled():
        raise HTTPException(status_code=503, detail="E-commerce integration is disabled.")
    if not SiteControl.is_customer_sync_enabled():
        raise OrderValidationError("Customer service is disabled.")
    if SiteControl.is_site_frozen():
        raise OrderValidationError("Store is under maintenance.")

    cart = payload.get("cart", [])
    if not cart:
        raise OrderValidationError("Cart cannot be empty")

    StockService.validate_cart_stock(cart)
    StockService.reserve_stock(cart)

    try:
        customer_id = get_or_create_customer(payload)
        items_payload = _prepare_items_payload(cart)
        address = payload.get("address", {})
        _validate_address(address)

        rfq_payload = {
            "doctype": settings.ECOM_RFQ_DOCTYPE,
            "customer_name": customer_id,
            "building_no": address.get("building_no"),
            "postal_code": address.get("postal_code"),
            "city": address.get("city"),
            "street_name": address.get("street_name"),
            "district": address.get("district"),
            "country": address.get("country"),
            "full_address": address.get("full_address"),
            "item_table": items_payload,
        }
        rfq_payload = {k: v for k, v in rfq_payload.items() if v not in (None, "", [])}

        try:
            res = erp_request(method="POST", path=f"/api/resource/{settings.ECOM_RFQ_DOCTYPE}", json=rfq_payload)
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

    finally:
        StockService.release_reservation(cart)


def create_sales_order(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create a Sales Order in ERPNext. Auto-submit if enabled.
    Ensures stock reservation safety.
    """
    if not SiteControl.is_website_integration_enabled():
        raise HTTPException(status_code=503, detail="E-commerce integration is disabled.")
    if not SiteControl.is_customer_sync_enabled():
        raise OrderValidationError("Customer service is disabled.")
    if SiteControl.is_site_frozen():
        raise OrderValidationError("Store is under maintenance.")

    cart = payload.get("cart", [])
    if not cart:
        raise OrderValidationError("Cart cannot be empty")

    StockService.validate_cart_stock(cart)
    StockService.reserve_stock(cart)

    try:
        customer_id = get_or_create_customer(payload)
        address = payload.get("address", {})
        warehouse = SiteControl.get_default_source_warehouse()
        if not warehouse:
            raise OrderValidationError("Default warehouse not configured.")

        items_payload = _prepare_items_payload(cart, warehouse)

        sales_order_payload = {
            "doctype": "Sales Order",
            "customer": customer_id,
            "transaction_date": _today(),
            "delivery_date": _today(),
            "selling_price_list": "Standard Selling",
            "items": items_payload,
            "address_display": address.get("full_address"),
        }

        try:
            res = erp_request(method="POST", path="/api/resource/Sales Order", json=sales_order_payload)
        except ERPError:
            raise OrderValidationError("Order service temporarily unavailable.")

        doc = res.get("data") or {}
        so_id = doc.get("name")

        # Auto-submit Sales Order if enabled
        if so_id and SiteControl.is_so_auto_submission_enabled():
            try:
                erp_request(method="POST", path=f"/api/resource/Sales Order/{so_id}/submit")
            except ERPError as e:
                # Log the error but leave as draft
                print(f"[WARN] Sales Order auto-submission failed for {so_id}: {e}")

        return {
            "status": "submitted",
            "ecommerce_rfq_id": so_id,
            "customer_id": customer_id,
            "created_at": _today(),
        }

    finally:
        StockService.release_reservation(cart)


def create_ecommerce_order(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Entry point: creates RFQ or Sales Order based on default order type."""
    order_type = SiteControl.get_default_order_type()
    if order_type == "E-Commerce RFQ":
        return create_ecommerce_rfq(payload)
    elif order_type == "Sales Order":
        return create_sales_order(payload)
    else:
        raise OrderValidationError("Invalid default order type.")
