from app.services.customer_service import find_customer_by_email, CustomerError
from app.integrations.erp_client import erp_request, ERPError


def get_profile(email: str):

    customer = find_customer_by_email(email)

    if not customer:
        return {
            "exists": False,
            "profile": None
        }

    return {
        "exists": True,
        "profile": {
            "customer_id": customer["name"],
            "customer_name": customer.get("customer_name"),
            "phone": customer.get("custom_phone_number"),
            "email": customer.get("custom_email"),
            "vat_number": customer.get("custom_vat_registration_number"),
        }
    }


def update_profile(email: str, payload: dict):

    customer = find_customer_by_email(email)

    if not customer:
        raise CustomerError("Customer not found.")

    customer_id = customer["name"]

    update_fields = {}

    if payload.get("customer_name"):
        update_fields["customer_name"] = payload["customer_name"]

    if payload.get("phone"):
        update_fields["custom_phone_number"] = payload["phone"]

    if payload.get("vat_number"):
        update_fields["custom_vat_registration_number"] = payload["vat_number"]

    try:
        erp_request(
            "PUT",
            f"/api/resource/Customer/{customer_id}",
            json=update_fields,
        )
    except ERPError:
        raise CustomerError("Profile update failed.")

    return {"status": "updated"}
