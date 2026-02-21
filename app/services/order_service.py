import json
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone

from app.core.config import settings
from app.integrations.erp_client import erp_request
from app.services.customer_service import get_or_create_customer


MAX_QTY_PER_ITEM = 1000


class OrderValidationError(ValueError):
    pass


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _get_item_min_fields(item_code: str) -> Dict[str, Any]:
    filters = [["item_code", "=", item_code]]
    fields = ["item_code", "item_name", "disabled", "is_sales_item", "stock_uom"]

    params = {
        "filters": json.dumps(filters),
        "fields": json.dumps(fields),
        "limit_page_length": 1,
    }

    res = erp_request("GET", "/api/resource/Item", params=params)
    rows = res.get("data", []) or []

    if not rows:
        raise OrderValidationError(f"Item not found: {item_code}")

    return rows[0]


def _get_selling_price(item_code: str) -> Optional[float]:
    filters = [["item_code", "=", item_code], ["selling", "=", 1]]

    params = {
        "filters": json.dumps(filters),
        "fields": json.dumps(["price_list_rate"]),
        "limit_page_length": 1,
        "order_by": "modified desc",
    }

    res = erp_request("GET", "/api/resource/Item%20Price", params=params)
    rows = res.get("data", []) or []

    if not rows:
        return None

    rate = rows[0].get("price_list_rate")

    return float(rate) if rate is not None else None


def preview_cart(cart: List[Dict[str, Any]]) -> Dict[str, Any]:

    if not cart:
        raise OrderValidationError("Cart cannot be empty")

    validated: List[Dict[str, Any]] = []
    total = 0.0

    for row in cart:
        item_code = row.get("item_code")
        qty = row.get("qty")

        if not item_code or qty is None:
            raise OrderValidationError("Invalid cart item")

        qty_f = float(qty)

        if qty_f <= 0:
            raise OrderValidationError("Quantity must be greater than zero")

        if qty_f > MAX_QTY_PER_ITEM:
            raise OrderValidationError("Quantity exceeds allowed limit")

        item = _get_item_min_fields(item_code)

        if int(item.get("disabled") or 0) == 1:
            raise OrderValidationError(f"Item {item_code} is disabled")

        if int(item.get("is_sales_item") or 0) != 1:
            raise OrderValidationError(f"Item {item_code} is not available for sale")

        rate = _get_selling_price(item_code)

        if rate is None:
            raise OrderValidationError(f"No selling price found for {item_code}")

        amount = qty_f * rate
        total += amount

        validated.append({
            "item_code": item_code,
            "item_name": item.get("item_name") or "",
            "quantity": qty_f,
            "unit_pricex": rate,
            "uom": item.get("stock_uom") or "Nos",
            "amount": amount,
        })

    return {"items": validated, "total": total}


def create_ecommerce_rfq(payload: Dict[str, Any]) -> Dict[str, Any]:

    customer_id = get_or_create_customer(payload)

    cart = payload.get("cart") or []

    preview = preview_cart(
        [{"item_code": x.get("item_code"), "qty": x.get("qty")} for x in cart]
    )

    item_rows = preview["items"]
    total = preview["total"]

    address = payload.get("address") or {}
    contact = payload.get("contact") or {}

    rfq_payload: Dict[str, Any] = {
        "customer_name": payload.get("customer_name"),
        "email_id": contact.get("email"),
        "company_name": payload.get("company_name") or payload.get("customer_name"),
        "phone_number": payload.get("phone"),
        "cr_no": payload.get("cr_no") or "",
        "vat_id": payload.get("vat_number"),

        "building_no": address.get("building_no") or "",
        "postal_code": address.get("postal_code") or "",
        "street_name": address.get("street_name") or "",
        "district": address.get("district") or "",
        "city": address.get("city") or "",
        "country": address.get("country") or "",
        "full_address": address.get("full_address") or "",

        settings.ECOM_RFQ_ITEM_TABLE_FIELD: item_rows,
        "notes": payload.get("notes", ""),
    }

    rfq_payload = {k: v for k, v in rfq_payload.items() if v is not None}

    res = erp_request(
        "POST",
        f"/api/resource/{settings.ECOM_RFQ_DOCTYPE_URL}",
        json=rfq_payload,
    )

    doc = res.get("data") or {}
    rfq_id = doc.get("name")

    if not rfq_id:
        raise OrderValidationError("E-Commerce RFQ creation failed")

    return {
        "status": "submitted",
        "message": "Your request has been submitted. Our team will review and contact you shortly.",
        "customer_id": customer_id,
        "ecommerce_rfq_id": rfq_id,
        "items": item_rows,
        "total": total,
        "created_at": _now_iso(),
    }