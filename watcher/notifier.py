"""Email alerts, sent via Gmail SMTP using an App Password."""

import smtplib
from email.message import EmailMessage

from . import config
from .retailers.base import ProductStatus

SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 587


def send_restock_alert(product: ProductStatus) -> None:
    subject = f"In stock: {product.title} ({product.retailer})"
    body = f"{product.title} is now in stock at {product.retailer}.\n\n{product.url}"
    _send_email(subject, body)


def send_broken_retailer_alert(retailer_name: str, consecutive_failures: int) -> None:
    subject = f"Stock watcher: {retailer_name} checker looks broken"
    body = (
        f"The {retailer_name} stock check has failed {consecutive_failures} times in a row.\n"
        "It may need its scraping logic updated (site layout change, new bot protection, etc.)."
    )
    _send_email(subject, body)


def _send_email(subject: str, body: str) -> None:
    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = config.GMAIL_ADDRESS
    message["To"] = ", ".join(config.ALERT_EMAIL_RECIPIENTS)
    message.set_content(body)

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as smtp:
        smtp.starttls()
        smtp.login(config.GMAIL_ADDRESS, config.GMAIL_APP_PASSWORD)
        smtp.send_message(message)
