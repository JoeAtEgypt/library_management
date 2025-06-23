# library/celery_periodic.py

from celery.schedules import crontab

CELERY_BEAT_SCHEDULE = {
    "send-due-soon-reminders-every-day": {
        "task": "library_management.library.tasks.send_due_soon_reminders",
        "schedule": crontab(minute=35, hour=21),  # 8:00 AM daily
    },
}
