from app.core.config import settings
from app.integrations.erp_client import erp_request, ERPError


def send_enquiry_email(
    full_name: str,
    email: str,
    inquiry_type: str,
    message: str,
) -> None:

    html_content = f"""
    <h3>New Website Enquiry</h3>
    <p><b>Name:</b> {full_name}</p>
    <p><b>Email:</b> {email}</p>
    <p><b>Type:</b> {inquiry_type}</p>
    <hr>
    <p>{message}</p>
    """

    erp_request(
        method="POST",
        path="/api/method/frappe.core.doctype.communication.email.make",
        json={
            "recipients": settings.SALES_EMAIL,
            "subject": f"Website Enquiry - {inquiry_type}",
            "content": html_content,
            "communication_medium": "Email",
            "send_email": 1,
            "reply_to": email  # 🔥 THIS IS THE FIX
        },
    )
