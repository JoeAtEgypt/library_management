import logging

from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail


@shared_task
def async_send_email(subject, message, receivers):
    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=receivers,
        )
    except Exception:
        logging.exception("Failed to send email")
        # Optionally, re-raise or handle as needed
