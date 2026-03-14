# app/notifications/notify.py

from fastapi import BackgroundTasks
from app.auth.otp import create_or_get_otp, verify_otp as otp_verify

# -------------------------
# Send OTP
# -------------------------
def send_otp(email: str, background_tasks: BackgroundTasks):
    """
    Creates OTP if none exists or expired, sends it asynchronously using BackgroundTasks.
    Returns status message.
    """
    otp = create_or_get_otp(email)
    if otp is None:
        return {"status": "waiting", "message": "OTP already sent recently"}

    # Background task to send OTP
    def _send_email():
        # Replace with actual email sending logic
        print(f"Sending OTP {otp} to {email}")
        # Example:
        # email_client.send_email(to=email, subject="Your OTP", body=f"Your OTP is {otp}")

    background_tasks.add_task(_send_email)

    return {"status": "sent", "message": "OTP sent successfully"}


# -------------------------
# Verify OTP
# -------------------------
def verify_otp(email: str, code: str):
    """
    Verifies the OTP.
    Returns {"status": "verified"} or {"status": "failed"}
    """
    if otp_verify(email, code):
        return {"status": "verified"}
    return {"status": "failed"}
