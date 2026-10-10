

import os

import json

from remainder_scheduler import start_reminder_scheduler

from datetime import date, datetime, timedelta

from zoneinfo import ZoneInfo

from dotenv import load_dotenv

from google import genai

from telegram import Update

from telegram.ext import (

    ApplicationBuilder,

    MessageHandler,

    ContextTypes,

    filters,

)

from database import (

    create_database,

    add_deadline,

    get_deadlines,

    get_deadline,

    update_deadline,

    save_calendar_event_id,

    delete_deadline,

    delete_all_deadlines,

)

from gcalendar import get_calendar_service

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

client = genai.Client(api_key=GEMINI_API_KEY)

TZ = ZoneInfo("Asia/Kolkata")

create_database()

async def handle_message(

    update: Update,

    context: ContextTypes.DEFAULT_TYPE,

):

    user_message = update.message.text.strip()

    command = user_message.lower()

    # Delete all deadlines: ask for confirmation first

    if command == "delete all":

        context.user_data["confirm_delete_all"] = True

        await update.message.reply_text(

            "⚠️ Are you sure you want to delete ALL deadlines?\n\n"

            "This will remove your saved deadlines and their linked "

            "Google Calendar events.\n\n"

            "Reply 'confirm delete all' to proceed, or 'cancel' to abort."

        )

        return

    # Confirm deleting all deadlines

    if command == "confirm delete all":

        if not context.user_data.get("confirm_delete_all"):

            await update.message.reply_text(

                "No pending delete-all request. Send 'delete all' first."

            )

            return

        context.user_data["confirm_delete_all"] = False

        try:

            service = get_calendar_service()

            deadlines = get_deadlines()

            deleted_count = 0

            calendar_errors = []

            for item in deadlines:

                deadline_id = item[0]

                record = get_deadline(deadline_id)

                if not record:

                    continue

                event_id = record[6]

                if event_id:

                    try:

                        service.events().delete(

                            calendarId="primary",

                            eventId=event_id

                        ).execute()

                    except Exception as e:

                        # A missing event is already effectively deleted.

                        # Other errors must stop database deletion.

                        if "404" not in str(e) and "410" not in str(e):

                            calendar_errors.append(

                                f"Deadline #{deadline_id}: {e}"

                            )

                            continue

                if delete_deadline(deadline_id):

                    deleted_count += 1

            if calendar_errors:

                await update.message.reply_text(

                    f"Deleted {deleted_count} deadline(s).\n"

                    f"{len(calendar_errors)} deadline(s) could not be "

                    "fully deleted from Google Calendar and were kept "

                    "in the database for safety.\n\n"

                    + "\n".join(calendar_errors[:3])

                )

            else:

                await update.message.reply_text(

                    f"✅ Done! Deleted {deleted_count} deadline(s) "

                    "and their linked Calendar events."

                )

        except Exception as e:

            print(f"Delete-all error: {e}")

            await update.message.reply_text(

                "Could not complete delete-all. Check the terminal "

                "for details."

            )

        return

    # Cancel delete-all confirmation

    if command == "cancel":

        if context.user_data.get("confirm_delete_all"):

            context.user_data["confirm_delete_all"] = False

            await update.message.reply_text(

                "Delete-all cancelled. Your deadlines were not changed."

            )

        else:

            await update.message.reply_text(

                "Nothing to cancel."

            )

        return

    # Delete one deadline

    if command.startswith("delete "):

        parts = user_message.split()

        if len(parts) != 2 or not parts[1].isdigit():

            await update.message.reply_text(

                "Use: delete ID\n"

                "Example: delete 3\n"

                "To delete everything, use 'delete all'."

            )

            return

        deadline_id = int(parts[1])

        record = get_deadline(deadline_id)

        if not record:

            await update.message.reply_text(

                f"No deadline found with ID {deadline_id}."

            )

            return

        event_id = record[6]

        try:

            if event_id:

                service = get_calendar_service()

                # Verify that the linked event exists.

                try:

                    event = service.events().get(

                        calendarId="primary",

                        eventId=event_id

                    ).execute()

                    print(

                        f"Deleting Calendar event: "

                        f"{event.get('summary')} | ID: {event_id}"

                    )

                    # Delete the event from Google Calendar.

                    service.events().delete(

                        calendarId="primary",

                        eventId=event_id

                    ).execute()

                    print("Google Calendar event deleted successfully.")

                except Exception as e:

                    status_code = getattr(

                        getattr(e, "resp", None),

                        "status",

                        None

                    )

                    print(

                        f"Calendar deletion failed. "

                        f"Event ID: {event_id} | "

                        f"Status: {status_code} | Error: {e}"

                    )

                    # If the event is already gone, continue deleting

                    # the database record. Otherwise, preserve the record.

                    if status_code not in (404, 410):

                        await update.message.reply_text(

                            "❌ Could not delete the Google Calendar event.\n"

                            f"Error: {e}\n\n"

                            "Your database record has been kept."

                        )

                        return

            else:

                print(

                    f"Deadline #{deadline_id} has no Calendar event ID."

                )

                await update.message.reply_text(

                    "⚠️ This deadline has no linked Calendar event ID.\n"

                    "The deadline was kept in the database."

                )

                return

            # Remove the database record only after Calendar deletion

            # succeeds or the event is confirmed to be already missing.

            deleted = delete_deadline(deadline_id)

            if deleted:

                await update.message.reply_text(

                    f"✅ Deadline #{deadline_id} deleted successfully.\n"

                    "Its linked Google Calendar event was also removed."

                )

            else:

                await update.message.reply_text(

                    "The Calendar event was removed, but the database "

                    "record could not be deleted. Check the terminal."

                )

        except Exception as e:

            print(f"Individual deletion error: {e}")

            await update.message.reply_text(

                "❌ Deletion failed. Check the terminal for details."

            )

        return

    # Edit an existing deadline

    if command.startswith("edit "):

        parts = user_message.split(maxsplit=3)

        if (

            len(parts) < 4

            or not parts[1].isdigit()

            or not parts[3].lower().startswith("to ")

        ):

            await update.message.reply_text(

                "Use: edit ID field to value\n"

                "Examples:\n"

                "edit 3 task to DSP Assignment\n"

                "edit 3 priority to High\n"

                "edit 3 deadline to 2026-10-20\n"

                "edit 3 deadline to 2026-10-20T22:00"

            )

            return

        deadline_id = int(parts[1])

        field = parts[2].strip().lower()

        new_value = parts[3][3:].strip()

        if not new_value:

            await update.message.reply_text(

                "Please provide a new value after 'to'."

            )

            return

        record = get_deadline(deadline_id)

        if not record:

            await update.message.reply_text(

                f"No deadline found with ID {deadline_id}."

            )

            return

        (

            record_id,

            old_task,

            old_deadline,

            old_priority,

            old_subtasks,

            status,

            event_id,

        ) = record

        if status != "Active":

            await update.message.reply_text(

                "Only active deadlines can be edited."

            )

            return

        new_task = old_task

        new_deadline = old_deadline

        new_priority = old_priority

        subtasks = old_subtasks.splitlines() if old_subtasks else []

        if field in ("task", "name"):

            new_task = new_value

        elif field == "priority":

            allowed_priorities = {

                "critical": "Critical",

                "high": "High",

                "medium": "Medium",

                "low": "Low",

            }

            if new_value.lower() not in allowed_priorities:

                await update.message.reply_text(

                    "Priority must be Critical, High, Medium, or Low."

                )

                return

            new_priority = allowed_priorities[new_value.lower()]

        elif field in ("deadline", "date", "time"):

            try:

                if field == "time":

                    if "T" in old_deadline:

                        date_part = old_deadline.split("T", 1)[0]

                    else:

                        date_part = old_deadline

                    parsed_time = datetime.strptime(

                        new_value, "%H:%M"

                    ).time()

                    new_deadline = (

                        f"{date_part}T{parsed_time.strftime('%H:%M')}"

                    )

                elif field in ("deadline", "date"):

                    try:

                        parsed_datetime = datetime.strptime(

                            new_value, "%Y-%m-%dT%H:%M"

                        )

                        new_deadline = parsed_datetime.strftime(

                            "%Y-%m-%dT%H:%M"

                        )

                    except ValueError:

                        parsed_date = datetime.strptime(

                            new_value, "%Y-%m-%d"

                        )

                        new_deadline = parsed_date.strftime("%Y-%m-%d")

            except ValueError:

                await update.message.reply_text(

                    "Invalid date or time.\n"

                    "Use YYYY-MM-DD for a date,\n"

                    "YYYY-MM-DDTHH:MM for a date and time,\n"

                    "or HH:MM when editing only the time."

                )

                return

            date_part = new_deadline.split("T", 1)[0]

            if date.fromisoformat(date_part) < date.today():

                await update.message.reply_text(

                    "That deadline is in the past. Please enter a future date."

                )

                return

        else:

            await update.message.reply_text(

                "Editable fields: task, priority, deadline, date, time."

            )

            return

        if not event_id:

            await update.message.reply_text(

                "This deadline has no linked Google Calendar event, "

                "so I cannot sync the edit."

            )

            return

        try:

            service = get_calendar_service()

            event = service.events().get(

                calendarId="primary",

                eventId=event_id

            ).execute()

            event["summary"] = new_task

            event["description"] = (

                f"Priority: {new_priority}\n"

                f"Status: Active\n"

                f"Managed by Deadline Agent\n"

                f"Deadline ID: {deadline_id}"

            )

            if "T" in new_deadline:

                event_start = datetime.strptime(

                    new_deadline, "%Y-%m-%dT%H:%M"

                ).replace(tzinfo=TZ)

                event_end = event_start + timedelta(hours=1)

                event["start"] = {

                    "dateTime": event_start.isoformat(),

                    "timeZone": "Asia/Kolkata",

                }

                event["end"] = {

                    "dateTime": event_end.isoformat(),

                    "timeZone": "Asia/Kolkata",

                }

            else:

                event_date = date.fromisoformat(new_deadline)

                event["start"] = {

                    "date": event_date.isoformat()

                }

                event["end"] = {

                    "date": (event_date + timedelta(days=1)).isoformat()

                }

            service.events().update(

                calendarId="primary",

                eventId=event_id,

                body=event

            ).execute()

            updated = update_deadline(

                deadline_id,

                new_task,

                new_deadline,

                new_priority,

                subtasks,

                event_id

            )

            if not updated:

                await update.message.reply_text(

                    "Google Calendar was updated, but the database "

                    "record was not. Please check the deadline."

                )

                return

            await update.message.reply_text(

                f"Deadline #{deadline_id} updated successfully!\n\n"

                f"Task: {new_task}\n"

                f"Deadline: {new_deadline}\n"

                f"Priority: {new_priority}\n"

                "Google Calendar has been updated."

            )

        except Exception as e:

            print(f"Edit error: {e}")

            await update.message.reply_text(

                "Could not update the deadline. "

                "Check the terminal for the error."

            )

        return

    # List saved deadlines

    if command == "show my deadlines":

        deadlines = get_deadlines()

        if not deadlines:

            await update.message.reply_text(

                "You have no active deadlines."

            )

            return

        reply = "📋 Your Deadlines:\n\n"

        for item in deadlines:

            task_id, task, deadline_date, priority, status = item

            reply += (

                f"🆔 {task_id}\n"

                f"📋 {task}\n"

                f"📅 {deadline_date}\n"

                f"🔥 {priority}\n"

                f"Status: {status}\n\n"

            )

        await update.message.reply_text(reply)

        return

    prompt = f"""

You are a deadline management assistant.

Today's date is {date.today().isoformat()}.

Timezone: Asia/Kolkata.

Extract deadline information from this message:

{user_message}

Return ONLY valid JSON:

{{

  "task": "task name or null",

  "deadline": "YYYY-MM-DD or null",

  "time": "HH:MM or null",

  "priority": "Critical/High/Medium/Low",

  "subtasks": ["subtask 1"],

  "needs_clarification": false

}}

Rules:

\- Never invent dates or times.

\- Resolve relative dates using today's date above.

\- Use 24-hour HH:MM for an explicitly specified time.

\- If no time was specified, return null for time.

\- If no deadline task exists, task must be null.

\- Return valid JSON without Markdown fences.

"""

    try:

        response = client.models.generate_content(

            model="gemini-3.5-flash-lite",

            contents=prompt,

        )

        result = json.loads(response.text)

        task = result.get("task")

        deadline = result.get("deadline")

        event_time = result.get("time")

        priority = result.get("priority", "Medium")

        subtasks = result.get("subtasks") or []

        needs_clarification = result.get(

            "needs_clarification", False

        )

        if not task or not isinstance(task, str):

            await update.message.reply_text(

                "I couldn't identify a deadline task. "

                "Please include the task name and due date."

            )

            return

        if not deadline:

            await update.message.reply_text(

                f"📋 Task: {task}\n"

                "📅 Date not confirmed. Please specify the due date."

            )

            return

        parsed_deadline = date.fromisoformat(deadline)

        if parsed_deadline < date.today():
            await update.message.reply_text(
                "⚠️ This date is in the past. Please confirm it."
            )
            return

        # Prevent duplicate active deadlines for the same task and date.
        # The current database stores the date only, not the event time.
        existing_deadlines = get_deadlines()
        normalized_task = " ".join(task.casefold().split())

        for existing in existing_deadlines:
            (
                existing_id,
                existing_task,
                existing_deadline,
                existing_priority,
                existing_status,
            ) = existing

            normalized_existing_task = " ".join(
                existing_task.casefold().split()
            )

            if (
                normalized_existing_task == normalized_task
                and existing_deadline[:10] == deadline
            ):
                await update.message.reply_text(
                    "⚠️ Possible duplicate deadline found.\n\n"
                    f"Existing ID: {existing_id}\n"
                    f"Task: {existing_task}\n"
                    f"Date: {existing_deadline}\n\n"
                    "I did not create another Google Calendar event."
                )
                return

        service = get_calendar_service()

        event = {

            "summary": task,

            "description": (

                f"Priority: {priority}\n"

                f"Subtasks: {', '.join(subtasks)}"

            ),

        }

        if event_time:

            parsed_time = datetime.strptime(

                event_time, "%H:%M"

            ).time()

            start_dt = datetime.combine(

                parsed_deadline, parsed_time, tzinfo=TZ

            )

            end_dt = start_dt + timedelta(hours=1)

            event["start"] = {

                "dateTime": start_dt.isoformat(),

                "timeZone": "Asia/Kolkata",

            }

            event["end"] = {

                "dateTime": end_dt.isoformat(),

                "timeZone": "Asia/Kolkata",

            }

        else:

            event["start"] = {"date": deadline}

            event["end"] = {

                "date": (

                    parsed_deadline + timedelta(days=1)

                ).isoformat()

            }

        # Create Calendar event, then save its ID in SQLite.

        created_event = service.events().insert(

            calendarId="primary",

            body=event,

        ).execute()

#save date and time togather for timed deadlines
        deadline_to_save = (
    f"{deadline}T{event_time}" if event_time else deadline
)
        try:

            add_deadline(

                task,

                deadline_to_save,

                priority,

                subtasks,

                calendar_event_id=created_event["id"],

            )

        except Exception:

            # Roll back the Calendar event if database saving fails.

            service.events().delete(

                calendarId="primary",

                eventId=created_event["id"],

            ).execute()

            raise

        reply = (

            "✅ Deadline saved!\n\n"

            f"📋 Task: {task}\n"

            f"📅 Date: {deadline}\n"

            f"🕒 Time: {event_time or 'All day'}\n"

            f"🔥 Priority: {priority}\n\n"

            "Subtasks:\n"

        )

        if subtasks:

            for subtask in subtasks:

                reply += f"• {subtask}\n"

        else:

            reply += "• None specified\n"

        if needs_clarification:

            reply += "\n⚠️ Some details may need confirmation."

        reply += "\n📅 Google Calendar event created."

        await update.message.reply_text(reply)

    except Exception as e:

        print("Error processing message:", repr(e))

        await update.message.reply_text(

            "Sorry, something went wrong. "

            "Check the VS Code terminal for details."

        )

app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

app.add_handler(

    MessageHandler(

        filters.TEXT & ~filters.COMMAND,

        handle_message,

    )

)

scheduler = start_reminder_scheduler()

print("Deadline Agent is running...")
app.run_polling()
