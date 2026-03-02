from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel, EmailStr
from app.core.config import settings
from app.integrations.erp_client import erp_request, ERPError

router = APIRouter()


# -----------------------------
# Request Model
# -----------------------------

class ContactRequest(BaseModel):
    fullName: str
    email: EmailStr
    inquiryType: str
    message: str


# -----------------------------
# Contact Endpoint
# -----------------------------

@router.post("/api/contact")
def submit_contact(payload: ContactRequest):

    try:
        # Build email content
        html_content = f"""
        <h3>New Website Enquiry</h3>
        <p><b>Name:</b> {payload.fullName}</p>
        <p><b>Email:</b> {payload.email}</p>
        <p><b>Type:</b> {payload.inquiryType}</p>
        <hr>
        <p>{payload.message}</p>
        """

        # Send email via ERPNext
        erp_request(
            method="POST",
            path="/api/method/frappe.core.doctype.communication.email.make",
            json={
                "recipients": settings.SALES_EMAIL,
                "subject": f"Website Enquiry - {payload.inquiryType}",
                "content": html_content,
                "communication_medium": "Email",
                "send_email": 1
            }
        )

        return {"success": True, "message": "Enquiry submitted successfully."}

    except ERPError as e:
        raise HTTPException(status_code=500, detail=str(e))

    except Exception:
        raise HTTPException(status_code=500, detail="Unexpected error occurred.")
