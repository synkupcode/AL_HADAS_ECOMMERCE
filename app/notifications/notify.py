# app/notifications/notify.py
from fastapi import BackgroundTasks
from app.auth.otp import create_or_get_otp, can_resend, _otp_store
from app.core.config import settings
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def _send_smtp_email(to_email: str, subject: str, html_content: str):
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = settings.SMTP_FROM_EMAIL
    msg["To"] = to_email
    part = MIMEText(html_content, "html")
    msg.attach(part)

    try:
        if settings.SMTP_USE_TLS:
            server = smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=10)
            server.starttls()
        else:
            server = smtplib.SMTP_SSL(settings.SMTP_HOST, settings.SMTP_PORT, timeout=10)

        server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
        server.sendmail(settings.SMTP_FROM_EMAIL, to_email, msg.as_string())
        server.quit()
    except Exception as e:
        print(f"Error sending email: {e}")

def send_otp(email: str, background_tasks: BackgroundTasks):
    if not can_resend(email):
        return {"status": "cooldown", "message": "Please wait before requesting new OTP."}

    otp = create_or_get_otp(email)
    if otp is None:
        otp = _otp_store[email]["otp_plain"]

    html_content = f"""
    <h3>Your Verification Code</h3>
    <h2 style="font-size:22px;">{otp}</h2>
    <p>Valid for 5 minutes.</p>
    """
    background_tasks.add_task(_send_smtp_email, to_email=email, subject="Your OTP Code", html_content=html_content)
    return {"status": "sent", "message": "OTP sent successfully."}

def verify_otp(email: str, code: str):
    from app.auth.otp import verify_otp as check
    if check(email, code):
        return {"status": "verified"}
    return {"status": "invalid"}
