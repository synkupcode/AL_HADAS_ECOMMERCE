# app/services/email_service.py
import logging
from fastapi import BackgroundTasks
from app.integrations.erp_client import erp_request

logger = logging.getLogger(__name__)

class EmailService:
    """
    Centralized service to send ERPNext emails using templates.
    All emails should be triggered through this service to ensure:
    - Async sending
    - Logging
    - Template consistency
    """

    @staticmethod
    def send_email(to_email: str, template_name: str, reference_doctype: str, reference_name: str, subject: str = None):
        """
        Send an email via ERPNext template.

        Args:
            to_email (str): Recipient email
            template_name (str): ERPNext Email Template name
            reference_doctype (str): ERPNext DocType to link the email
            reference_name (str): Doc name (ID) to link
            subject (str, optional): Optional override of template subject
        """
        payload = {
            "recipients": to_email,
            "reference_doctype": reference_doctype,
            "reference_name": reference_name,
            "send_email": 1,
            "template_name": template_name
        }
        if subject:
            payload["subject"] = subject

        try:
            erp_request(
                method="POST",
                path="/api/method/frappe.core.doctype.communication.email.make",
                json=payload
            )
            logger.info(f"Email sent to {to_email} using template '{template_name}' for {reference_doctype} {reference_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to send email to {to_email} using template '{template_name}': {str(e)}")
            return False

    @staticmethod
    def send_email_async(background_tasks: BackgroundTasks, **kwargs):
        """
        Send email asynchronously using FastAPI BackgroundTasks.
        Usage:
            send_email_async(background_tasks, to_email=..., template_name=..., reference_doctype=..., reference_name=...)
        """
        background_tasks.add_task(EmailService.send_email, **kwargs)

    # --- Predefined template helpers for easier usage ---
    @staticmethod
    def send_rfq_received(background_tasks: BackgroundTasks, rfq_doc):
        EmailService.send_email_async(
            background_tasks,
            to_email=rfq_doc.customer_email,
            template_name="RFQ Received",
            reference_doctype="E-Commerce RFQ",
            reference_name=rfq_doc.name
        )

    @staticmethod
    def send_sales_order_confirmation(background_tasks: BackgroundTasks, sales_order):
        EmailService.send_email_async(
            background_tasks,
            to_email=sales_order.customer_email,
            template_name="Sales Order Confirmation",
            reference_doctype="Sales Order",
            reference_name=sales_order.name
        )

    @staticmethod
    def send_invoice_generated(background_tasks: BackgroundTasks, invoice):
        EmailService.send_email_async(
            background_tasks,
            to_email=invoice.customer_email,
            template_name="Invoice Generated",
            reference_doctype="Sales Invoice",
            reference_name=invoice.name
        )

    @staticmethod
    def send_order_shipped(background_tasks: BackgroundTasks, order):
        EmailService.send_email_async(
            background_tasks,
            to_email=order.customer_email,
            template_name="Order Shipped",
            reference_doctype="Sales Order",
            reference_name=order.name
        )
