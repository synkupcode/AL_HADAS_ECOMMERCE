from app.auth.otp import create_or_get_otp, can_resend
from app.core.config import settings
from app.integrations.erp_client import erp_request


def send_otp(email: str):

    if not can_resend(email):
        return {
            "status": "cooldown",
            "message": "Please wait before requesting new OTP."
        }

    otp = create_or_get_otp(email)

    if otp is None:
        return {
            "status": "existing",
            "message": "OTP already valid."
        }

    html_content = f"""
    <h3>Your Verification Code</h3>
    <h2>{otp}</h2>
    <p>Valid for 5 minutes.</p>
    """

    erp_request(
        method="POST",
        path="/api/method/frappe.core.doctype.communication.email.make",
        json={
            "recipients": email,
            "subject": "Your OTP Code",
            "content": html_content,
            "communication_medium": "Email",
            "send_email": 1
        }
    )

    return {"status": "sent"}


def verify_otp(email: str, code: str):
    from app.auth.otp import verify_otp as check

    if check(email, code):
        return {"status": "verified"}

    return {"status": "invalid"}
