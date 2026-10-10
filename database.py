
import sqlite3

from datetime import datetime

DB_NAME = "deadlines.db"


def create_database():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS deadlines (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task TEXT NOT NULL,
            deadline TEXT,
            priority TEXT,
            subtasks TEXT,
            status TEXT DEFAULT 'Active'
        )
    """)

    # Add the Calendar event ID to existing databases safely.
    cursor.execute("PRAGMA table_info(deadlines)")
    columns = [column[1] for column in cursor.fetchall()]

   
    if "calendar_event_id" not in columns:
        cursor.execute("""
            ALTER TABLE deadlines
            ADD COLUMN calendar_event_id TEXT
        """)

    # Track reminders already sent.
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sent_reminders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            deadline_id INTEGER NOT NULL,
            reminder_type TEXT NOT NULL,
            sent_at TEXT NOT NULL,
            UNIQUE(deadline_id, reminder_type)
        )
    """)

    conn.commit()
    conn.close()


def add_deadline(task, deadline, priority, subtasks,
                 calendar_event_id=None):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO deadlines
        (task, deadline, priority, subtasks, calendar_event_id)
        VALUES (?, ?, ?, ?, ?)
    """, (
        task,
        deadline,
        priority,
        "\n".join(subtasks or []),
        calendar_event_id
    ))

    deadline_id = cursor.lastrowid
    conn.commit()
    conn.close()

    return deadline_id


def get_deadlines():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, task, deadline, priority, status
        FROM deadlines
        WHERE status = 'Active'
        ORDER BY deadline, id
    """)

    deadlines = cursor.fetchall()
    conn.close()

    return deadlines


def get_deadline(deadline_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, task, deadline, priority, subtasks,
               status, calendar_event_id
        FROM deadlines
        WHERE id = ?
    """, (deadline_id,))

    deadline = cursor.fetchone()
    conn.close()

    return deadline


def update_deadline(deadline_id, task, deadline, priority,
                    subtasks, calendar_event_id=None):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE deadlines
        SET task = ?, deadline = ?, priority = ?,
            subtasks = ?, calendar_event_id = ?
        WHERE id = ? AND status = 'Active'
    """, (
        task,
        deadline,
        priority,
        "\n".join(subtasks or []),
        calendar_event_id,
        deadline_id
    ))

    updated = cursor.rowcount > 0
    conn.commit()
    conn.close()

    return updated


def save_calendar_event_id(deadline_id, event_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE deadlines
        SET calendar_event_id = ?
        WHERE id = ?
    """, (event_id, deadline_id))

    conn.commit()
    conn.close()


def delete_deadline(deadline_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        DELETE FROM deadlines
        WHERE id = ?
    """, (deadline_id,))

    deleted = cursor.rowcount > 0
    conn.commit()
    conn.close()

    return deleted


def delete_all_deadlines():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("DELETE FROM deadlines")

    deleted_count = cursor.rowcount
    conn.commit()
    conn.close()

    return deleted_count

def reminder_already_sent(deadline_id, reminder_type="day_before"):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT 1 FROM sent_reminders
        WHERE deadline_id = ? AND reminder_type = ?
    """, (deadline_id, reminder_type))

    result = cursor.fetchone()
    conn.close()

    return result is not None


def record_reminder_sent(deadline_id, reminder_type="day_before"):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    try:
        cursor.execute("""
            INSERT INTO sent_reminders
            (deadline_id, reminder_type, sent_at)
            VALUES (?, ?, ?)
        """, (
            deadline_id,
            reminder_type,
            datetime.now().isoformat(timespec="seconds")
        ))

        conn.commit()
        return True

    except sqlite3.IntegrityError:
        return False

    finally:
        conn.close()

