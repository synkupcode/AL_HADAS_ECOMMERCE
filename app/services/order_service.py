from datetime import datetime, timezone
from typing import Dict, Any, List

from app.core.config import settings
from app.integrations.erp_client import erp_request
from app.services.customer_service import get_or_create_customer
from app.services.ecommerce.ecommerce_engine import EcommerceEngine


class OrderValidationError(ValueError):
    pass


def _now_date():
    return datetime.now(timezone.utc).date().isoformat()


# -------------------------------------------------
# FETCH ORDER TYPE FROM ERP (SAFE WITH FALLBACK)
# -------------------------------------------------
def _get_default_order_type() -> str:
    """
    Fetch default order type from ERP E-Commerce Settings.
    Falls back to RFQ if anything fails.
    """

    try:
        res = erp_request(
            "GET",
            "/api/resource/E-Commerce Settings/1tk6cucvc9",
            params={"fields": '["default_order_type"]'},
        )

        doc = res.get("data") or {}
        order_type = doc.get("default_order_type")

        if order_type in ("Sales Order", settings.ECOM_RFQ_DOCTYPE):
            return order_type

    except Exception:
        # Do not break checkout if settings fetch fails
        pass

    return settings.ECOM_RFQ_DOCTYPE


# -------------------------------------------------
# ITEM FETCHING & PRICE RESOLUTION
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


def _resolve_checkout_price(item_code: str) -> float:

    item = _fetch_item_from_erp(item_code)

    transformed = EcommerceEngine.transform_item(item)

    if not transformed["is_price_visible"]:
        raise OrderValidationError(
            f"Price is hidden for item {item_code}"
        )

    price = transformed["price"]

    if price is None:
        raise OrderValidationError(
            f"No valid price available for item {item_code}"
        )

    return float(price)


# -------------------------------------------------
# MAIN ORDER CREATION FUNCTION
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

    # ------------------------------------------
    # DETERMINE ORDER TYPE FROM ERP
    # ------------------------------------------
    order_type = _get_default_order_type()

    # ------------------------------------------
    # SALES ORDER FLOW
    # ------------------------------------------
    if order_type == "Sales Order":

        sales_payload = {
            "doctype": "Sales Order",
            "customer": customer_id,
            "items": [
                {
                    "item_code": i["item_code"],
                    "qty": i["quantity"],
                    "rate": i["unit_pricex"],
                }
                for i in items_payload
            ],
        }

        res = erp_request(
            "POST",
            "/api/resource/Sales Order",
            json=sales_payload,
        )

    # ------------------------------------------
    # E-COMMERCE RFQ FLOW (EXISTING LOGIC)
    # ------------------------------------------
    else:

        rfq_payload = {
            "doctype": settings.ECOM_RFQ_DOCTYPE,
            "customer_name": customer_id,
            "email_id": payload.get("contact", {}).get("email"),
            "mobile_no": payload.get("phone"),
            "building_no": payload.get("address", {}).get("building_no"),
            "postal_code": payload.get("address", {}).get("postal_code"),
            "street_name": payload.get("address", {}).get("street_name"),
            "district": payload.get("address", {}).get("district"),
            "city": payload.get("address", {}).get("city"),
            "country": payload.get("address", {}).get("country"),
            "full_address": payload.get("address", {}).get("full_address"),
            settings.ECOM_RFQ_ITEM_TABLE_FIELD: items_payload,
        }

        rfq_payload = {
            k: v for k, v in rfq_payload.items()
            if v not in (None, "", [])
        }

        res = erp_request(
            "POST",
            f"/api/resource/{settings.ECOM_RFQ_DOCTYPE}",
            json=rfq_payload,
        )

    # ------------------------------------------
    # COMMON RESPONSE
    # ------------------------------------------
    doc = res.get("data") or {}
    doc_name = doc.get("name")

    if not doc_name:
        raise OrderValidationError("Order creation failed")

    return {
        "status": "submitted",
        "ecommerce_rfq_id": doc_name,  # kept same to avoid frontend break
        "customer_id": customer_id,
        "created_at": _now_date(),
    }
