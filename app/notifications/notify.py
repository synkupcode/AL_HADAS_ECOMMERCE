# app/notifications/notify.py

from app.auth.otp import create_or_get_otp, can_resend
from app.core.config import settings
from app.services.email_service import send_email


def send_otp(email: str):
    """
    Generate or reuse OTP and send it via SMTP immediately.
    Returns a dictionary with status: 'sent', 'cooldown', or 'existing'.
    """
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
    <h2 style="font-size:22px;">{otp}</h2>
    <p>Valid for 5 minutes.</p>
    """

    # Send OTP directly using SMTP settings
    send_email(
        to_email=email,
        subject="Your OTP Code",
        html_content=html_content
    )

    return {"status": "sent"}


def verify_otp(email: str, code: str):
    """
    Verify OTP code for a given email.
    Returns dictionary with status: 'verified' or 'invalid'.
    """
    from app.auth.otp import verify_otp as check

    if check(email, code):
        return {"status": "verified"}

    return {"status": "invalid"}
