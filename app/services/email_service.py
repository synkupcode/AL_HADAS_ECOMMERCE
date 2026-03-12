# app/services/email_service.py

import logging
from fastapi import BackgroundTasks
from app.integrations.erp_client import erp_request

logger = logging.getLogger(__name__)


class EmailService:
    """
    Centralized service to send ERPNext emails using templates.

    Business emails (RFQ, Sales Order, Invoice, Shipping etc.)
    should be triggered through ERPNext Notification system.
    """

    @staticmethod
    def send_email(
        to_email: str,
        template_name: str,
        reference_doctype: str,
        reference_name: str,
        subject: str = None
    ):
        """
        Send an email via ERPNext template.

        Args:
            to_email: recipient email
            template_name: ERPNext Email Template
            reference_doctype: linked document type
            reference_name: linked document name
            subject: optional subject override
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

            logger.info(
                f"Email sent to {to_email} using template '{template_name}' "
                f"for {reference_doctype} {reference_name}"
            )

            return True

        except Exception as e:
            logger.error(
                f"Failed to send email to {to_email} "
                f"using template '{template_name}': {str(e)}"
            )
            return False

    @staticmethod
    def send_email_async(background_tasks: BackgroundTasks, **kwargs):
        """
        Send email asynchronously using FastAPI BackgroundTasks.
        """
        background_tasks.add_task(EmailService.send_email, **kwargs)

    # ------------------------------------------------
    # ERP TEMPLATE HELPERS
    # ------------------------------------------------

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


# ------------------------------------------------
# OTP EMAIL FUNCTION (Used by notify.py)
# ------------------------------------------------
def send_email(to_email: str, subject: str, html_content: str):
    """
    Direct email sender used ONLY for OTP emails.
    """

    payload = {
        "recipients": to_email,
        "subject": subject,
        "content": html_content,
        "send_email": 1
    }

    try:
        erp_request(
            method="POST",
            path="/api/method/frappe.core.doctype.communication.email.make",
            json=payload
        )

        logger.info(f"OTP email sent to {to_email}")
        return True

    except Exception as e:
        logger.error(f"OTP email failed for {to_email}: {str(e)}")
        return False
