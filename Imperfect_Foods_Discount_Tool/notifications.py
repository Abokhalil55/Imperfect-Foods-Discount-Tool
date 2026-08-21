import os
import smtplib
from email.message import EmailMessage

from dotenv import load_dotenv

load_dotenv(override=True)


def _send_email(receiver_email, subject, body):
    """Send one email synchronously through the configured Gmail account."""
    sender_email = (os.getenv("sender_email") or "").strip()
    app_password = (os.getenv("Google_app_pass") or "").replace(" ", "").strip()

    if not sender_email or not app_password:
        raise RuntimeError("Email service is not configured on the server.")

    message = EmailMessage()
    message["From"] = sender_email
    message["To"] = receiver_email
    message["Subject"] = subject
    message.set_content(body)

    with smtplib.SMTP("smtp.gmail.com", 587, timeout=20) as server:
        server.ehlo()
        server.starttls()
        server.ehlo()
        server.login(sender_email, app_password)
        server.send_message(message)

    print(f"Email sent successfully to {receiver_email}: {subject}")
    return True


def send_interest_confirmation_email(email, store_location, interested_in):
    """Confirm that a customer's stock-interest request was saved."""
    subject = "JimatRasa stock alert saved"
    body = (
        "Hello!\n\n"
        f"We have saved your interest in {interested_in} for {store_location}.\n"
        "We will email you when a matching item is newly listed there.\n\n"
        "JimatRasa"
    )
    return _send_email(email, subject, body)


def send_notification_email(email, store_location, interested_in, store_name):
    """Notify a customer when a newly listed item matches a saved interest."""
    subject = "JimatRasa: matching food is now available"
    body = (
        "Hello!\n\n"
        f"A new item matching your interest in {interested_in} is now available in {store_location}.\n"
        f"Seller: {store_name}\n\n"
        "Open JimatRasa to view the current item, price and remaining stock.\n\n"
        "JimatRasa"
    )
    return _send_email(email, subject, body)
