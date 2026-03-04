from typing import Dict, Any, List

from app.core.config import settings
from app.integrations.erp_client import erp_request, ERPError
from app.services.customer_service import find_customer_by_email


def get_user_orders(email: str, limit: int = 20, offset: int = 0) -> Dict[str, Any]:
    """
    Returns unified order history:
    - Sales Orders
    - E-Commerce RFQs
    """

    # -----------------------------------------
    # Find Customer (READ ONLY)
    # -----------------------------------------
    customer = find_customer_by_email(email)

    if not customer:
        return {
            "success": True,
            "data": {
                "orders": [],
                "total": 0,
            },
        }

    customer_id = customer["name"]

    orders: List[Dict[str, Any]] = []

    # =========================================
    # SALES ORDERS
    # =========================================
    try:
        sales_res = erp_request(
            method="GET",
            path="/api/resource/Sales Order",
            params={
                "fields": '["name","transaction_date","grand_total","currency"]',
                "filters": [["customer", "=", customer_id]],
                "order_by": "creation desc",
            },
        )
    except ERPError:
        sales_res = {"data": []}

    for so in sales_res.get("data", []):
        orders.append(
            {
                "id": so.get("name"),
                "order_type": "sales_order",
                "date": so.get("transaction_date"),
                "grand_total": so.get("grand_total"),
                "currency": so.get("currency"),
            }
        )

    # =========================================
    # E-COMMERCE RFQs
    # =========================================
    try:
        rfq_res = erp_request(
            method="GET",
            path=f"/api/resource/{settings.ECOM_RFQ_DOCTYPE}",
            params={
                "fields": '["name","creation","grand_total","currency"]',
                "filters": [["customer_name", "=", customer_id]],
                "order_by": "creation desc",
            },
        )
    except ERPError:
        rfq_res = {"data": []}

    for rfq in rfq_res.get("data", []):
        orders.append(
            {
                "id": rfq.get("name"),
                "order_type": "ecommerce_rfq",
                "date": rfq.get("creation"),
                "grand_total": rfq.get("grand_total", 0),
                "currency": rfq.get("currency", "AED"),
            }
        )

    # =========================================
    # SORT (Newest First)
    # =========================================
    orders.sort(key=lambda x: x["date"] or "", reverse=True)

    total = len(orders)

    # Pagination
    paginated_orders = orders[offset : offset + limit]

    return {
        "success": True,
        "data": {
            "orders": paginated_orders,
            "total": total,
        },
    }
