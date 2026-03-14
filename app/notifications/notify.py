# app/notifications/notify.py

import os
import smtplib
from email.message import EmailMessage
from fastapi import BackgroundTasks
from app.auth.otp import create_or_get_otp, verify_otp as otp_verify

SMTP_HOST = os.getenv("SMTP_HOST")
SMTP_PORT = int(os.getenv("SMTP_PORT", "465"))
SMTP_USERNAME = os.getenv("SMTP_USERNAME")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
SMTP_USE_TLS = os.getenv("SMTP_USE_TLS", "false").lower() == "true"
SMTP_FROM_EMAIL = os.getenv("SMTP_FROM_EMAIL")


# ---------------------
# Send OTP
# ---------------------
def send_otp(email: str, background_tasks: BackgroundTasks):

    otp = create_or_get_otp(email)

    if otp is None:
        return {
            "status": "sent",
            "message": "OTP already sent. Please wait."
        }

    background_tasks.add_task(_send_email, email, otp)

    return {
        "status": "sent",
        "message": "OTP sent successfully"
    }


# ---------------------
# Email sender
# ---------------------
def _send_email(to_email: str, otp: str):

    msg = EmailMessage()
    msg["Subject"] = "Your OTP Code"
    msg["From"] = SMTP_FROM_EMAIL
    msg["To"] = to_email
    msg.set_content(
        f"Your OTP code is: {otp}\n\n"
        "This code is valid for 5 minutes."
    )

    try:

        # PORT 465 = SSL
        if SMTP_PORT == 465:

            with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT) as server:
                server.login(SMTP_USERNAME, SMTP_PASSWORD)
                server.send_message(msg)

        # PORT 587 = TLS
        else:

            with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:

                if SMTP_USE_TLS:
                    server.starttls()

                server.login(SMTP_USERNAME, SMTP_PASSWORD)
                server.send_message(msg)

        print(f"OTP email sent to {to_email}")

    except Exception as e:

        print(f"SMTP ERROR sending OTP to {to_email}: {e}")


# ---------------------
# Verify OTP
# ---------------------
def verify_otp(email: str, code: str):

    if otp_verify(email, code):
        return {"status": "verified"}

    return {"status": "failed"}
