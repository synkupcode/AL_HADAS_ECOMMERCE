# app/notifications/notify.py

import smtplib
import asyncio
from email.mime.text import MIMEText
from core.config import settings


def send_email_sync(to_email: str, subject: str, html_content: str):
    """
    Sends email immediately via SMTP (blocking).
    """
    msg = MIMEText(html_content, 'html')
    msg['Subject'] = subject
    msg['From'] = settings.SMTP_FROM_EMAIL
    msg['To'] = to_email

    with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as smtp:
        if settings.SMTP_USE_TLS:
            smtp.starttls()
        smtp.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
        smtp.send_message(msg)


async def send_email_async(to_email: str, subject: str, html_content: str):
    """
    Sends email asynchronously using background thread.
    """
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, send_email_sync, to_email, subject, html_content)
