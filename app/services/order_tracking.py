import json
from typing import Any, Dict

from app.core.config import settings
from app.integrations.erp_client import erp_request


def list_orders_by_phone(phone_number: str, limit: int = 50) -> Dict[str, Any]:

    if limit > 100:
        limit = 100

    filters = [["phone_number", "=", phone_number]]

    fields = [
        "name",
        "creation",
        "modified",
        "customer_name",
        "email_id",
        "phone_number",
        "vat_id",
        "payment_mode",
        "transaction_id",
        "paid_amount",
        "payment_date",
    ]

    params = {
        "filters": json.dumps(filters),
        "fields": json.dumps(fields),
        "order_by": "modified desc",
        "limit_page_length": limit,
    }

    res = erp_request(
        "GET",
        f"/api/resource/{settings.ECOM_RFQ_DOCTYPE_URL}",
        params=params,
    )

    return {
        "status": "success",
        "orders": res.get("data", []) or [],
    }


def get_order_detail(rfq_id: str) -> Dict[str, Any]:

    res = erp_request(
        "GET",
        f"/api/resource/{settings.ECOM_RFQ_DOCTYPE_URL}/{rfq_id}",
    )

    return {
        "status": "success",
        "data": res.get("data") or {},
    }