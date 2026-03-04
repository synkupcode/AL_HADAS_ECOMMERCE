from app.services.customer_service import (
    find_customer_by_email,
    get_or_create_customer,
    CustomerError,
)
from app.integrations.erp_client import erp_request, ERPError


# ==========================================
# GET PROFILE
# ==========================================
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


# ==========================================
# UPDATE PROFILE (UPSERT SAFE VERSION)
# ==========================================
def update_profile(email: str, payload: dict):

    # 1️⃣ Create OR Get Customer
    # IMPORTANT:
    # get_or_create_customer() now returns a STRING (customer_id)
    try:
        customer_id = get_or_create_customer({
            "email": email,
            "customer_name": payload.get("customer_name"),
            "phone": payload.get("phone"),
            "vat_number": payload.get("vat_number"),
        })
    except Exception:
        raise CustomerError("Customer creation failed.")

    # 2️⃣ Prepare update fields (only if provided)
    update_fields = {}

    if payload.get("customer_name"):
        update_fields["customer_name"] = payload["customer_name"]

    if payload.get("phone"):
        update_fields["custom_phone_number"] = payload["phone"]

    if payload.get("vat_number"):
        update_fields["custom_vat_registration_number"] = payload["vat_number"]

    # 3️⃣ If nothing to update, return success
    if not update_fields:
        return {"status": "updated"}

    # 4️⃣ Update ERP Customer
    try:
        erp_request(
            "PUT",
            f"/api/resource/Customer/{customer_id}",
            json=update_fields,
        )
    except ERPError:
        raise CustomerError("Profile update failed.")

    return {"status": "updated"}
