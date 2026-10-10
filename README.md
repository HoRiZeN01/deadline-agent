# Deadline Agent 📅

**An AI-powered Telegram assistant for managing deadlines, organising tasks, and keeping Google Calendar in sync.**

Deadline Agent turns natural-language messages into structured deadlines using Google's Gemini API. It stores deadline information locally, creates corresponding Google Calendar events, and sends email reminders before deadlines.

## ✨ Features

- **Natural-language input:** Describe tasks and deadlines conversationally.
- **AI-powered parsing:** Uses Google Gemini to extract deadline details, priorities, and subtasks.
- **Google Calendar integration:** Creates and updates linked calendar events.
- **Email reminders:** Sends a reminder approximately one day before a deadline through Gmail.
- **Persistent storage:** Stores deadlines in a local SQLite database.
- **Deadline management:** List, edit, and delete saved deadlines.
- **Safe bulk deletion:** Requires confirmation before deleting all deadlines.
- **Time-zone awareness:** Handles dates and times using the Asia/Kolkata time zone.

## 🛠️ Tech Stack

| Technology          | Purpose                        |
| ------------------- | ------------------------------ |
| Python              | Application logic              |
| Telegram Bot API    | Chat interface                 |
| Google Gemini API   | Natural-language understanding |
| Google Calendar API | Calendar event management      |
| Gmail API           | Email reminders                |
| SQLite              | Local database                 |
| APScheduler         | Periodic reminder checks       |

## 🧠 How It Works

1. Send a message describing a task to the Telegram bot.
2. Gemini helps extract the task, deadline, priority, and subtasks.
3. The application saves the deadline in SQLite.
4. A corresponding event is created or synchronised with Google Calendar.
5. The reminder scheduler checks upcoming deadlines and sends eligible email reminders.

**Reminder policy:** The intended behaviour is one email reminder approximately 24 hours before a deadline, with no separate reminder on the deadline day.

## 📁 Project Structure

```text
deadline-agent/
├── bot.py                  # Telegram bot and message handling
├── database.py             # SQLite database operations
├── gcalendar.py            # Google Calendar and OAuth setup
├── gmail_service.py        # Gmail service and email sending
├── reminder_scheduler.py   # Scheduled reminder checks
├── requirements.txt        # Python dependencies
├── .env.example            # Environment variable template
├── .gitignore              # Excludes secrets and local files
└── README.md               # Project documentation
```

## 🚀 Getting Started

### Prerequisites

- Python 3.10 or later
- A Telegram bot token from [BotFather](https://t.me/BotFather)
- A Google Gemini API key from [Google AI Studio](https://aistudio.google.com/)
- A Google Cloud project with the Google Calendar API and Gmail API enabled
- A Google OAuth 2.0 Desktop application client

### 1. Clone the repository

```bash
git clone https://github.com/HoRiZeN1/deadline-agent.git
cd deadline-agent
```

### 2. Create a virtual environment

**Windows:**

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
```

If PowerShell blocks activation, use Command Prompt:

```bat
.venv\Scripts\activate.bat
```

### 3. Install dependencies

```bash
python -m pip install -r requirements.txt
```

### 4. Configure environment variables

Create a local `.env` file based on `.env.example` and fill in your own values.

```env
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
GEMINI_API_KEY=your_gemini_api_key
```

Never commit your real `.env` file.

### 5. Configure Google OAuth

1. Open the [Google Cloud Console](https://console.cloud.google.com/).
2. Select your project and enable the Google Calendar API and Gmail API.
3. Configure the OAuth consent screen.
4. Create an OAuth client with application type **Desktop app**.
5. Download the OAuth client JSON file and save it as `credentials.json` in the project root.
6. Run the Google service setup or test flow provided by the project to complete authorisation in your browser.

The application uses Google OAuth to access the connected calendar and send email through Gmail. The authorised credentials are stored locally in `token.json`.

Keep `credentials.json` and `token.json` private. Do not upload them to GitHub.

### 6. Run the bot

```bash
python bot.py
```

Keep the process running for the Telegram bot and scheduled reminder checks to remain active.

## 💬 Example Messages

Examples of the intended natural-language interaction:

- `Remind me to submit my DSP assignment on 20 October at 10 PM.`
- `Add a high-priority task to finish my project report by Friday.`
- `Show my deadlines.`
- `Edit 3 priority to High.`
- `Delete 3.`
- `Delete all`

The exact details Gemini extracts depend on the message and the application's current parsing logic.

## 🔐 Security

- API keys and tokens belong in local environment files or other secure configuration.
- Google OAuth credentials must remain private.
- The SQLite database contains personal task information and should not be committed.
- Use a private repository if you prefer not to share the source code publicly.

## ☁️ Deployment

Cloud deployment is a planned next step. The current local version requires a running Python process for continuous Telegram polling and scheduled reminders. Any cloud deployment must also preserve the SQLite database and provide secure access to the required credentials.

## 🗺️ Roadmap

- [x] Telegram bot foundation
- [x] Gemini-powered task parsing
- [x] SQLite deadline storage
- [x] Google Calendar integration
- [x] Gmail email sending
- [x] Scheduled reminder system
- [x] Verify reminder delivery across different deadline scenarios
- [x] Free cloud deployment with persistent storage
- [x] Improve reliability and error handling
- [x] Add automated tests

## 👨‍💻 Author

**Horizen** — Electronics and Communication Engineering student interested in Python, AI, automation, and practical software projects.

GitHub: [@HoRiZeN1](https://github.com/HoRiZeN1)

---

*Built as a practical project exploring AI-assisted productivity and automation.*
