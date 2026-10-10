
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from apscheduler.schedulers.background import BackgroundScheduler

from database import (
    get_deadlines,
    reminder_already_sent,
    record_reminder_sent,
)
from gmail_service import send_reminder_email

TZ = ZoneInfo("Asia/Kolkata")

# Replace this with the Gmail address you authorized.
REMINDER_EMAIL = "rupamalpha@gmail.com"


def check_deadline_reminders():
    now = datetime.now(TZ)
    window_start = now + timedelta(hours=24)
    window_end = window_start + timedelta(minutes=15)

    for item in get_deadlines():
        deadline_id, task, deadline, priority, status = item

        try:
            if "T" in deadline:
                due = datetime.strptime(
                    deadline, "%Y-%m-%dT%H:%M"
                ).replace(tzinfo=TZ)
            else:
                # All-day deadlines are due at 9 AM local time.
                due = datetime.strptime(
                    deadline, "%Y-%m-%d"
                ).replace(hour=9, tzinfo=TZ)

            if window_start <= due < window_end:
                if reminder_already_sent(deadline_id):
                    continue

                send_reminder_email(
                    REMINDER_EMAIL,
                    task,
                    due.strftime("%d %b %Y, %I:%M %p"),
                    priority,
                )

                if record_reminder_sent(deadline_id):
                    print(f"Reminder email sent for deadline #{deadline_id}")

        except Exception as e:
            print(f"Reminder error for deadline #{deadline_id}: {e}")


def start_reminder_scheduler():
    scheduler = BackgroundScheduler(timezone=TZ)
    scheduler.add_job(
        check_deadline_reminders,
        trigger="interval",
        minutes=15,
        id="deadline_email_reminders",
        replace_existing=True,
        max_instances=1,
    )
    scheduler.start()
    print("Email reminder scheduler started.")
    return scheduler
