# EliteUniteTime - Team Productivity & Time Management System

A complete production-ready time management and team productivity platform built for Bale messenger bot. Track working hours, manage penalties, generate reports, and discover teammates' profiles.

## 🚀 Features

### Core Features
- **Daily Time Reporting**: Users submit main and secondary working hours
- **Group Integration**: Automatic summary notifications to group chat
- **Smart Penalty System**: Automatic penalties for missed reports (checked daily at 10 AM)
- **Weekly & Monthly Reports**: Comprehensive statistics and analytics
- **User Profiles**: Social discovery system with bio and interests
- **Admin Panel**: Full administrative controls and reporting

### Technical Features
- ✅ Timezone-aware (Iran/Tehran)
- ✅ Jalali (Shamsi) calendar support for Persian users
- ✅ SQLite database with proper schema
- ✅ Scheduled tasks with APScheduler
- ✅ Type hints and comprehensive documentation
- ✅ Clean modular architecture
- ✅ Excel export for BI reports
- ✅ User state management for multi-step flows

## 📋 Project Structure

```
EliteUniteTime/
├── app.py                 # Main entry point
├── bot.py                 # Bot initialization and routing
├── requirements.txt       # Python dependencies
├── .env.example          # Environment variables template
│
├── config/
│   └── settings.py       # Configuration and constants
│
├── database/
│   └── db.py             # SQLite manager and operations
│
├── models/
│   └── models.py         # Data classes (User, Report, Penalty, etc)
│
├── services/
│   ├── penalty.py        # Penalty management
│   ├── reports.py        # Report generation and statistics
│   └── scheduler.py      # APScheduler jobs
│
├── handlers/
│   ├── start.py          # /start and registration
│   ├── tasks.py          # Daily report submission
│   ├── profile.py        # User profiles and social discovery
│   └── admin.py          # Admin panel functions
│
├── utils/
│   ├── date_utils.py     # Timezone and Jalali conversions
│   └── formatter.py      # Message formatting
│
├── data/
│   └── database.db       # SQLite database (auto-created)
│
└── logs/
    └── app.log           # Application logs
```

## 🛠 Installation & Setup

### Prerequisites
- Python 3.11+
- pip package manager
- Bale bot API token (from @BaleBot)

### Step 1: Clone/Setup Project

```bash
cd EliteUniteTime
```

### Step 2: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 3: Configuration

Copy `.env.example` to `.env` and fill in your values:

```bash
cp .env.example .env
```

Edit `.env`:
```
BALE_API_TOKEN=your_token_from_bale_bot
BALE_GROUP_ID=your_group_chat_id
BALE_ADMIN_IDS=admin_user_id_1,admin_user_id_2
```

### Step 4: Run the Bot

```bash
python app.py
```

You should see:
```
==================================================
EliteUniteTime Bot Starting...
==================================================
```

## 📖 User Guide

### For Regular Users

#### 1. Registration (`/start`)
- Send `/start` command
- Enter your full name
- Share your phone number
- Receive main menu

#### 2. Daily Report (`📊 ثبت گزارش روزانه`)
- Click "Daily Report" button
- Bot shows today's date in Persian
- Enter main working hours (0-12)
- Enter secondary hours (0-8)
- Report saved and posted to group

#### Example Daily Report:
```
👤 Amir Hossein Ghadimi
📌 اصلی: 6
📌 فرعی: 2
➕ مجموع: 8
📅 1405/02/07 - دوشنبه
```

#### 3. View Reports
- **Weekly Report** (`📈 گزارش هفتگی`): Last 7 days summary
- **Monthly Report** (`📅 گزارش ماهانه`): Current month total

#### 4. User Profile (`👤 پروفایل من`)
- View/edit your bio
- Add interests (sports, learning, etc)
- Share profile with other users

#### 5. Social Discovery (`👥 آشنایی با دوستان`)
- Browse other users' profiles
- View bio and interests
- Discover teammates

### For Admins

#### Admin Panel (`/admin`)

**1. View All Users** (`👥 مشاهده تمام کاربران`)
- List all registered users
- Show phone numbers
- Get total user count

**2. Weekly Summary** (`📊 گزارش هفتگی`)
- All users' hours for the week
- Total hours, averages
- Team statistics

**3. Export Excel** (`📈 دانلود Excel`)
- Download Excel file with all data
- Columns: Name | Main Hours | Side Hours | Total | Penalties | Date
- Ready for business intelligence

**4. Manage Penalties** (`⚠️ مدیریت تنبیهات`)
- View unpaid penalties
- Mark penalties as paid
- Track missing reports

**5. Manual Check** (`🔄 بررسی دستی`)
- Manually trigger penalty check
- Create penalties for missed reports
- Useful for testing

## ⏰ Penalty System

### How it Works

1. **Automatic Check**: Every day at 10:00 AM (Iran time)
2. **Scope**: Checks yesterday's reports
3. **Action**: Creates penalty for users without report
4. **Notification**: User is notified about penalty
5. **Status**: Can be marked as "paid" by admin

### Example
- **User**: Ahmad hasn't reported for 2023-02-06
- **Check Time**: 2023-02-07 at 10:00 AM
- **Result**: Penalty created for Ahmad
- **Message**: "You missed reporting for 1405/02/06"

## 📊 Database Schema

### users
```sql
- id (INTEGER PRIMARY KEY)
- bale_id (INTEGER UNIQUE)
- full_name (TEXT)
- phone (TEXT)
- bio (TEXT)
- interests (TEXT)
- created_at (TIMESTAMP)
- updated_at (TIMESTAMP)
```

### reports
```sql
- id (INTEGER PRIMARY KEY)
- user_id (INTEGER FOREIGN KEY)
- date_shamsi (TEXT) - Format: YYYY/MM/DD
- date_gregorian (TEXT) - Format: YYYY-MM-DD
- main_hours (REAL)
- side_hours (REAL)
- total_hours (REAL)
- created_at (TIMESTAMP)
- updated_at (TIMESTAMP)
- UNIQUE(user_id, date_gregorian)
```

### penalties
```sql
- id (INTEGER PRIMARY KEY)
- user_id (INTEGER FOREIGN KEY)
- date_shamsi (TEXT)
- date_gregorian (TEXT)
- amount (INTEGER)
- reason (TEXT)
- status (TEXT) - 'unpaid' or 'paid'
- created_at (TIMESTAMP)
```

## 🔧 Services & Architecture

### Database Service (`database/db.py`)
- **User Operations**: Add, get, update, list users
- **Report Operations**: Submit, retrieve, query reports
- **Penalty Operations**: Create, manage, query penalties
- **Analytics**: Get missing reports, statistics

### Report Service (`services/reports.py`)
- **Daily Reports**: Submit and retrieve daily reports
- **Weekly Reports**: Calculate weekly statistics
- **Monthly Reports**: Calculate monthly statistics
- **Excel Export**: Prepare data for export

### Penalty Service (`services/penalty.py`)
- **Penalty Creation**: Create penalties for missing reports
- **Penalty Queries**: Get user penalties
- **Summary**: Generate penalty reports

### Scheduler Service (`services/scheduler.py`)
- **APScheduler Integration**: Background task scheduling
- **Cron Triggers**: Daily checks at specific times
- **Job Management**: Start, stop, monitor jobs

## 🕐 Timezone & Calendar

### Timezone Handling
- **System Timezone**: Asia/Tehran (Iran)
- **Storage**: Gregorian dates in database
- **Display**: Jalali (Shamsi) dates to users

### Example Conversion
```python
from utils.date_utils import gregorian_to_jalali_str, format_date_persian

# Gregorian to Jalali
date_str = gregorian_to_jalali_str(date(2024, 4, 27))  # Returns: "1403/02/08"

# With day name
formatted = format_date_persian(date(2024, 4, 27))  # Returns: "شنبه 1403/02/08"
```

## 📝 Code Examples

### Submitting a Report
```python
from services.reports import ReportService
from database.db import Database

db = Database()
report_service = ReportService(db)

success, message = report_service.submit_daily_report(
    user_id=1,
    main_hours=6.5,
    side_hours=2,
)

if success:
    print("Report saved!")
```

### Checking Penalties
```python
from services.penalty import PenaltyService
from database.db import Database

db = Database()
penalty_service = PenaltyService(db)

unpaid = penalty_service.get_user_unpaid_penalties(user_id=1)
for penalty in unpaid:
    print(f"Unpaid: {penalty.reason}")
```

### Getting Weekly Stats
```python
from services.reports import ReportService
from database.db import Database

db = Database()
report_service = ReportService(db)

stats = report_service.get_weekly_stats(user_id=1)
print(f"Week Total: {stats.total_hours} hours")
print(f"Days Reported: {stats.days_reported}")
```

## 🔐 Admin Configuration

### Setting Admin Users

In your `.env` file:
```
BALE_ADMIN_IDS=123456789,987654321
```

Admins can:
- ✅ View all users
- ✅ Generate reports
- ✅ Export Excel
- ✅ Manage penalties
- ✅ Trigger manual checks

## 🐛 Troubleshooting

### Bot Won't Start
```
Error: BALE_API_TOKEN is not set
```
**Solution**: Add `BALE_API_TOKEN` to your `.env` file

### Database Error
```
sqlite3.OperationalError: database is locked
```
**Solution**: Close all other connections to `data/database.db`

### Scheduler Not Running
```
Scheduler failed to start
```
**Solution**: Check `logs/app.log` for detailed errors

### Message Encoding Issues
```
UnicodeEncodeError: 'utf-8' codec can't encode character
```
**Solution**: Usually automatic with Python 3.11+, ensure UTF-8 locale

## 📈 Performance Notes

- **Database**: SQLite is suitable for teams up to ~1000 users
- **Scheduler**: APScheduler uses one thread, minimal CPU overhead
- **Messages**: Batch processing recommended for large groups
- **Excel Export**: Can handle 500+ rows without issues

For larger deployments, consider:
- PostgreSQL for database
- Redis for caching
- Celery for async tasks

## 📚 API Reference

### Key Classes

#### Database
```python
from database.db import Database

db = Database()
user = db.get_user_by_bale_id(bale_id)
reports = db.get_reports_by_user_and_date(user_id, start, end)
penalties = db.get_penalties_by_user(user_id)
```

#### ReportService
```python
from services.reports import ReportService

service = ReportService(db)
stats = service.get_daily_stats()
weekly = service.get_weekly_stats(user_id)
monthly = service.get_monthly_stats(user_id)
```

#### PenaltyService
```python
from services.penalty import PenaltyService

service = PenaltyService(db)
created = service.check_and_create_missing_report_penalties()
unpaid = service.get_user_unpaid_penalties(user_id)
```

## 🎨 Customization

### Change Penalty Check Time
In `config/settings.py`:
```python
MISSING_REPORT_CHECK_HOUR = 10  # Change to desired hour (0-23)
MISSING_REPORT_CHECK_MINUTE = 0  # Change to desired minute
```

### Change Hour Limits
In `config/settings.py`:
```python
MAX_MAIN_HOURS = 12
MAX_SIDE_HOURS = 8
MAX_TOTAL_HOURS = 20
```

### Custom Messages
In `config/settings.py`:
```python
MESSAGES = {
    "welcome": "Your custom welcome message",
    "enter_name": "Your custom prompt",
    # ... more messages
}
```

## 📄 License

This project is built as a complete time management system for team productivity.

## 🤝 Support

For issues or improvements:
1. Check `logs/app.log` for error messages
2. Review database schema in `database/db.py`
3. Check handler implementations for flow logic
4. Validate timezone settings in `utils/date_utils.py`

## 📞 Contact

For questions about the system architecture or implementation, refer to the code comments and docstrings throughout the project.

---

**Version**: 1.0.0  
**Last Updated**: April 2026  
**Status**: Production Ready ✅
