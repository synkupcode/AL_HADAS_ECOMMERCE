import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from app.core.config import settings


def send_email(to_email: str, subject: str, html_content: str):

    if not settings.SMTP_HOST:
        raise Exception("SMTP not configured")

    msg = MIMEMultipart()
    msg["From"] = settings.SMTP_FROM_EMAIL
    msg["To"] = to_email
    msg["Subject"] = subject

    msg.attach(MIMEText(html_content, "html"))

    server = smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT)

    if settings.SMTP_USE_TLS:
        server.starttls()

    server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)

    server.send_message(msg)
    server.quit()
