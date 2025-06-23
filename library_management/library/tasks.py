import logging
from datetime import timedelta

from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone

from library_management.library.models import BorrowedBook
from library_management.users.tasks import async_send_email


@shared_task
def send_due_soon_reminders():
    now = timezone.now()
    in_3_days = now + timedelta(days=3)

    borrowed_books = BorrowedBook.objects.select_related(
        "transaction", "transaction__user", "book"
    ).filter(return_due__range=(now, in_3_days), returned_at__isnull=True)

    for item in borrowed_books:
        print(item.return_due)
        user = item.transaction.user
        days_left = (item.return_due.date() - now.date()).days
        name = user.get_full_name() or getattr(user, "username", None) or user.email
        subject = f"Reminder: Return your books in {days_left} day(s)"
        message = (
            f"Hello {name},\n\n"
            f"This is a friendly reminder that the following book is due to be "
            f"returned in {days_left} day(s): {item.book.title}\n\n"
            f"Return Date: {item.return_due.date()}\n\n"
            "Please return them on time to avoid penalties.\n\n"
            "Regards,\n"
            "Library Management Team"
        )

        try:
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
            )
        except Exception:
            logging.exception("Failed to send email")
