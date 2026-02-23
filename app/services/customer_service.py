from typing import Optional
import json
from app.core.config import settings
from app.integrations.erp_client import erp_request


def get_customer_id_by_phone(phone: str) -> Optional[str]:
    """
    Searches Customer by phone.

    NOTE:
    This only works if phone is stored in Customer
    as a custom field (e.g., phone or mobile_number).

    If you follow ERPNext standard design,
    phone should be searched in Contact instead.
    """

    if not phone:
        return None

    # Use configured field name
    filters = [settings.CUSTOMER_PHONE_FIELD, "=", phone]

    res = erp_request(
        "GET",
        "/api/resource/Customer",
        params={
            "filters": json.dumps(filters),
            "fields": json.dumps(["name"]),
        },
    )

    data = res.get("data") or []

    if data:
        return data[0].get("name")

    return None
