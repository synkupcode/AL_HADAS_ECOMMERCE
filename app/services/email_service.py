import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from app.core.config import settings


from app.integrations.erp_client import erp_request


def send_email(to_email: str, subject: str, html_content: str):

    erp_request(
        method="POST",
        path="/api/method/frappe.core.doctype.communication.email.make",
        json={
            "recipients": to_email,
            "subject": subject,
            "content": html_content,
            "communication_medium": "Email",
            "send_email": 1
        }
    )
