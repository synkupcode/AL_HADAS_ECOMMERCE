from typing import Dict, Any

from app.integrations.erp_client import erp_request, ERPError
from app.core.config import settings


def get_order_detail(order_id: str, order_type: str) -> Dict[str, Any]:
    """
    Returns full order details from ERP.
    Supports:
    - sales_order
    - ecommerce_rfq
    """

    try:
        # -------------------------
        # SALES ORDER
        # -------------------------
        if order_type == "sales_order":
            res = erp_request(
                method="GET",
                path=f"/api/resource/Sales Order/{order_id}",
            )

        # -------------------------
        # E-COMMERCE RFQ
        # -------------------------
        elif order_type == "ecommerce_rfq":
            res = erp_request(
                method="GET",
                path=f"/api/resource/{settings.ECOM_RFQ_DOCTYPE}/{order_id}",
            )

        else:
            return {
                "success": False,
                "message": "Invalid order type",
            }

        data = res.get("data", {})

        # Remove sensitive fields if needed
        data.pop("delivery_date", None)  # skipping for now

        return {
            "success": True,
            "data": data,
        }

    except ERPError:
        return {
            "success": False,
            "message": "Order not found",
        }
