from gcalendar import get_calendar_service
from datetime import datetime, timedelta


service = get_calendar_service()

start_time = datetime.now() + timedelta(minutes=10)
end_time = start_time + timedelta(minutes=30)

event = {
    "summary": "Deadline Agent Test",
    "description": "Test event created by my Deadline Agent.",
    "start": {
        "dateTime": start_time.isoformat(),
        "timeZone": "Asia/Kolkata",
    },
    "end": {
        "dateTime": end_time.isoformat(),
        "timeZone": "Asia/Kolkata",
    },
}

created_event = service.events().insert(
    calendarId="primary",
    body=event
).execute()

print("Calendar event created:")
print(created_event.get("htmlLink"))