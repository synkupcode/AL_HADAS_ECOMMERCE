# app/notifications/notify.py

import os
import smtplib
from email.mime.text import MIMEText
from fastapi import BackgroundTasks
from app.auth.otp import create_or_get_otp, verify_otp

# -----------------------
# Environment Variables
# -----------------------
SMTP_HOST = os.getenv("SMTP_HOST")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
EMAIL_FROM = os.getenv("EMAIL_FROM")


# -----------------------
# Send OTP via email
# -----------------------
def send_otp(email: str, background_tasks: BackgroundTasks) -> dict:
    """
    Generates or reuses OTP and sends via email asynchronously.
    """

    otp = create_or_get_otp(email)
    if otp is None:
        return {"status": "waiting", "message": "OTP already sent. Please wait before requesting again."}

    # Schedule email sending in background
    background_tasks.add_task(_send_email, email, otp)

    return {"status": "sent", "message": f"OTP sent to {email}"}


def _send_email(to_email: str, otp: str):
    """
    Sends the actual email using SMTP credentials from env.
    """
    subject = "Your OTP Code"
    body = f"Your OTP code is: {otp}\n\nThis code is valid for 5 minutes."

    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = EMAIL_FROM
    msg["To"] = to_email

    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.sendmail(EMAIL_FROM, to_email, msg.as_string())
    except Exception as e:
        # Optionally log the error
        print(f"Error sending email to {to_email}: {e}")


# -----------------------
# Verify OTP
# -----------------------
def verify_otp(email: str, code: str) -> dict:
    """
    Verifies OTP against in-memory store.
    """
    if verify_otp(email, code):
        return {"status": "verified", "message": "OTP verified successfully"}
    else:
        return {"status": "failed", "message": "Invalid or expired OTP"}
