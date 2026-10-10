
import base64
from email.message import EmailMessage

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

SCOPES = [
    "https://www.googleapis.com/auth/calendar.events",
    "https://www.googleapis.com/auth/gmail.send",
]



def get_gmail_service():
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build

    creds = Credentials.from_authorized_user_file("token.json")

    if not creds.valid and creds.refresh_token:
        creds.refresh(Request())

    print("Token file:", creds.token is not None)
    print("Gmail scope:", creds.has_scopes([
        "https://www.googleapis.com/auth/gmail.send"
    ]))

    return build(
        "gmail",
        "v1",
        credentials=creds,
        cache_discovery=False,
    )



def send_reminder_email(recipient, task, deadline, priority):
    service = get_gmail_service()

    message = EmailMessage()
    message["To"] = recipient
    message["Subject"] = f"Deadline reminder: {task}"
    message.set_content(
        f"Your deadline is approximately 24 hours away.\n\n"
        f"Task: {task}\n"
        f"Deadline: {deadline}\n"
        f"Priority: {priority}\n"
    )

    encoded = base64.urlsafe_b64encode(
        message.as_bytes()
    ).decode()

    service.users().messages().send(
        userId="me",
        body={"raw": encoded},
    ).execute()
