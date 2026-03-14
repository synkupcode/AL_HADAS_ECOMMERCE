# app/notifications/notify.py

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from app.auth.otp import create_or_get_otp, can_resend
from app.core.config import settings

# -----------------------------
# Send OTP Email via Direct SMTP
# -----------------------------
def send_otp(email: str):
    """
    Sends OTP to the provided email.
    Resends same OTP if still valid (5 min validity, 1 min cooldown).
    """

    if not can_resend(email):
        return {
            "status": "cooldown",
            "message": "Please wait before requesting new OTP."
        }

    otp = create_or_get_otp(email)

    if otp is None:
        # Valid OTP already exists, retrieve it from store
        from app.auth.otp import _otp_store
        otp = _otp_store[email]["otp_plain"]
        return {
            "status": "existing",
            "message": "OTP is still valid.",
            "otp_sent": True  # optional, can be removed
        }

    # Compose email
    subject = "Your OTP Verification Code"
    html_content = f"""
    <h3>Your Verification Code</h3>
    <h2 style="font-size:22px;">{otp}</h2>
    <p>Valid for 5 minutes.</p>
    """

    # Direct SMTP send
    try:
        msg = MIMEMultipart("alternative")
        msg["From"] = settings.SMTP_FROM_EMAIL
        msg["To"] = email
        msg["Subject"] = subject
        msg.attach(MIMEText(html_content, "html"))

        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
            if settings.SMTP_USE_TLS:
                server.starttls()
            server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
            server.sendmail(settings.SMTP_FROM_EMAIL, email, msg.as_string())

    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to send OTP email: {e}"
        }

    return {
        "status": "sent",
        "message": "OTP sent successfully."
    }


# -----------------------------
# Verify OTP
# -----------------------------
def verify_otp(email: str, code: str):
    from app.auth.otp import verify_otp as check

    if check(email, code):
        return {"status": "verified"}

    return {"status": "invalid"}
