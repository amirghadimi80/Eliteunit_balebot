# EliteUniteTime - System Architecture & Design

## 🏗 Architecture Overview

EliteUniteTime follows a **clean, modular architecture** with clear separation of concerns:

```
┌─────────────────────────────────────────────┐
│           Bale Bot Interface                │
│    (Balethon Client - Message Handler)      │
└────────────────┬────────────────────────────┘
                 │
┌─────────────────▼────────────────────────────┐
│         Handlers Layer (input routing)        │
├──────────────────────────────────────────────┤
│ • StartHandler     → Registration & /start   │
│ • TaskHandler      → Daily reports           │
│ • ProfileHandler   → User profiles & social  │
│ • AdminHandler     → Admin functions         │
└────────────────┬────────────────────────────┘
                 │
┌─────────────────▼────────────────────────────┐
│        Services Layer (business logic)        │
├──────────────────────────────────────────────┤
│ • ReportService    → Generate reports       │
│ • PenaltyService   → Manage penalties       │
│ • SchedulerService → Background jobs        │
└────────────────┬────────────────────────────┘
                 │
┌─────────────────▼────────────────────────────┐
│       Database Layer (data persistence)       │
├──────────────────────────────────────────────┤
│ • Database class   → SQLite operations      │
│   - User CRUD operations                    │
│   - Report CRUD operations                  │
│   - Penalty management                      │
└────────────────┬────────────────────────────┘
                 │
┌─────────────────▼────────────────────────────┐
│         Data Layer (SQLite Database)         │
├──────────────────────────────────────────────┤
│ • users table      → User registration      │
│ • reports table    → Daily submissions      │
│ • penalties table  → Missed reports         │
└──────────────────────────────────────────────┘

┌──────────────────────────────────────────────┐
│      Utility Layer (helpers & formatting)     │
├──────────────────────────────────────────────┤
│ • date_utils.py    → Timezone & Jalali      │
│ • formatter.py     → Message formatting     │
│ • models.py        → Data classes           │
└──────────────────────────────────────────────┘
```

## 📦 Module Responsibilities

### Core Modules

#### `bot.py` - Main Bot Class
**Purpose**: Central bot orchestrator and message router  
**Responsibilities**:
- Initialize all handlers and services
- Register message and callback event handlers
- Route incoming messages to appropriate handlers
- Manage bot lifecycle (start/stop)
- Error handling and logging

**Key Methods**:
- `_handle_message()`: Routes text messages
- `_handle_callback_query()`: Routes button clicks
- `start()`: Launch bot
- `stop()`: Graceful shutdown

**Flow**:
```
Message arrives → _handle_message() → Route to handler → Handler processes → Response sent
```

#### `app.py` - Application Entry Point
**Purpose**: Main entry point for running the system  
**Responsibilities**:
- Check environment configuration
- Initialize bot
- Handle application lifecycle
- Error handling and graceful shutdown

**Flow**:
```
python app.py → app.main() → EliteUniteTimeBot() → bot.start() → Client.run()
```

### Handler Modules

#### `handlers/start.py` - StartHandler
**Purpose**: User registration and onboarding  
**State Machine**:
```
(Initial)
  ↓
[waiting_name] → User enters name
  ↓
[waiting_phone] → User shares contact
  ↓
User created in database
  ↓
Main menu shown ✅
```

**Key Methods**:
- `handle_start()`: Entry point for /start
- `_start_registration()`: Begin registration flow
- `handle_name_input()`: Process name input
- `handle_phone_input()`: Process phone contact
- `_show_main_menu()`: Display main menu

**Database Operations**:
- Check if user exists
- Create new user record
- Retrieve user profile

#### `handlers/tasks.py` - TaskHandler
**Purpose**: Daily report submission and statistics  
**State Machine**:
```
User clicks "Daily Report"
  ↓
[waiting_main_hours] → User enters main hours
  ↓
[waiting_side_hours] → User enters side hours
  ↓
Report validated & saved
  ↓
Notification sent to group ✅
```

**Key Methods**:
- `handle_daily_report_start()`: Initiate report flow
- `handle_main_hours_input()`: Process main hours
- `handle_side_hours_input()`: Process side hours & submit
- `handle_weekly_report()`: Generate weekly report
- `handle_monthly_report()`: Generate monthly report

**Validation**:
- Hours must be positive
- Main hours: 0-12
- Side hours: 0-8
- No duplicate reports for same date

#### `handlers/profile.py` - ProfileHandler
**Purpose**: User profiles and social discovery  
**Features**:
- View own profile
- Edit bio and interests
- Discover other users
- View other users' profiles

**Key Methods**:
- `handle_profile_view()`: Show user's profile
- `handle_edit_profile()`: Edit menu
- `handle_edit_bio()`: Edit biography
- `handle_edit_interests()`: Edit interests
- `handle_friends_discovery()`: Browse users
- `handle_view_user_profile()`: View another user

**Privacy**:
- Phone numbers only shown to own profile
- Public bios visible to all
- Interests visible to all

#### `handlers/admin.py` - AdminHandler
**Purpose**: Administrative functions and reporting  
**Features**:
- View all users
- Generate reports
- Export Excel
- Manage penalties
- Manual penalty check

**Permission Check**:
```python
user_id in BALE_ADMIN_IDS → Admin access ✅
```

**Key Methods**:
- `check_admin_permission()`: Verify admin status
- `handle_admin_panel()`: Show admin menu
- `handle_view_all_users()`: List all users
- `handle_weekly_report_admin()`: Team weekly report
- `handle_export_excel()`: Excel export
- `handle_penalties_management()`: Penalty summary
- `handle_manual_penalty_check()`: Manual trigger

### Service Modules

#### `services/reports.py` - ReportService
**Purpose**: Report generation and analytics  
**Responsibility**: All calculations and statistics

**Report Types**:
1. **Daily Report**
   - Submit and retrieve
   - Validation (hours, duplicates)
   - Group notification

2. **Weekly Report**
   - Last 7 days summary
   - Total hours per category
   - Days reported count

3. **Monthly Report**
   - Current month total
   - Days reported vs available
   - Completion percentage

**Key Methods**:
- `submit_daily_report()`: Save daily submission
- `get_today_all_reports()`: Retrieve today's reports
- `get_daily_stats()`: Calculate daily statistics
- `get_weekly_stats()`: Calculate weekly stats
- `get_monthly_stats()`: Calculate monthly stats
- `get_excel_export_data()`: Prepare Excel data

**Calculations**:
```
total_hours = main_hours + side_hours
avg_per_user = total_hours / num_reports
completion_rate = days_reported / days_total * 100
```

#### `services/penalty.py` - PenaltyService
**Purpose**: Penalty management for missed reports  
**Workflow**:

```
Daily at 10 AM (Iran time)
  ↓
Check yesterday's reports
  ↓
Find users without reports
  ↓
Create penalty records
  ↓
Update penalty status to "unpaid"
  ↓
Notify users
```

**Key Methods**:
- `check_and_create_missing_report_penalties()`: Trigger check
- `get_user_unpaid_penalties()`: List unpaid
- `get_user_all_penalties()`: List all
- `mark_penalty_as_paid()`: Mark as paid
- `get_total_unpaid_penalty_count()`: Count penalties
- `get_user_missing_dates()`: List missing dates
- `get_all_unpaid_penalties_summary()`: Team summary

**Penalty Record**:
```python
Penalty(
    user_id=1,
    date_shamsi="1405/02/06",
    date_gregorian="2024-04-26",
    reason="عدم ثبت گزارش روز 1405/02/06",
    amount=1,
    status="unpaid"  # or "paid"
)
```

#### `services/scheduler.py` - SchedulerService
**Purpose**: Background task scheduling using APScheduler  
**Architecture**:

```
APScheduler (BackgroundScheduler)
  ↓
CronTrigger (Daily at 10:00 AM)
  ↓
_check_missing_reports() job
  ↓
PenaltyService.check_and_create_missing_report_penalties()
  ↓
Notify users & admins
```

**Key Methods**:
- `start()`: Start scheduler
- `stop()`: Stop scheduler
- `set_bot_instance()`: Set bot for notifications
- `_add_missing_report_check_job()`: Register daily job
- `_check_missing_reports()`: Execute check
- `trigger_manual_check()`: Manual execution
- `get_jobs()`: List active jobs
- `is_running()`: Check status

**Cron Configuration**:
```python
trigger = CronTrigger(
    hour=10,  # 10 AM
    minute=0,  # 00 minutes
    timezone="Asia/Tehran"
)
```

### Database Module

#### `database/db.py` - Database Class
**Purpose**: All database operations and persistence  
**Design**: Singleton pattern (one connection manager)

**User Operations**:
- `user_exists()`: Check existence
- `add_user()`: Create new
- `get_user_by_bale_id()`: Retrieve by Bale ID
- `get_user_by_id()`: Retrieve by user ID
- `get_all_users()`: Retrieve all
- `update_user()`: Modify profile

**Report Operations**:
- `report_exists()`: Check if reported today
- `add_report()`: Submit new report
- `get_report_by_id()`: Retrieve by ID
- `get_reports_by_user_and_date()`: Range query
- `get_reports_by_date()`: Daily reports
- `get_missing_report_users()`: Find who didn't report

**Penalty Operations**:
- `add_penalty()`: Create penalty
- `get_penalties_by_user()`: User's penalties
- `mark_penalty_paid()`: Update status
- `get_missing_report_users()`: For penalty check

**Connection Management**:
```python
def get_connection() → sqlite3.Connection
  ├─ Open connection to database.db
  ├─ Set row_factory = sqlite3.Row (dict-like rows)
  └─ Return connection
```

### Models Module

#### `models/models.py` - Data Classes
**Purpose**: Type-safe data structures  
**Design**: Dataclasses with auto-initialization

**Core Models**:

1. **User**
   ```python
   @dataclass
   class User:
       bale_id: int
       full_name: str
       phone: Optional[str] = None
       bio: Optional[str] = None
       interests: Optional[str] = None
       id: Optional[int] = None
       created_at: Optional[datetime] = None
   ```

2. **Report**
   ```python
   @dataclass
   class Report:
       user_id: int
       date_shamsi: str  # "1405/02/07"
       date_gregorian: str  # "2024-04-27"
       main_hours: float = 0.0
       side_hours: float = 0.0
       total_hours: float = 0.0  # Calculated in __post_init__
   ```

3. **Penalty**
   ```python
   @dataclass
   class Penalty:
       user_id: int
       date_shamsi: str
       date_gregorian: str
       reason: str
       amount: int = 1
       status: str = "unpaid"  # "unpaid" or "paid"
   ```

4. **Stats Models**
   - `DailyStats`: Daily group statistics
   - `WeeklyStats`: User weekly statistics
   - `MonthlyStats`: User monthly statistics
   - `UserProfile`: Extended profile info

### Utility Modules

#### `utils/date_utils.py` - Date Utilities
**Purpose**: Timezone and calendar conversions  
**Iran-Specific Features**:
- Timezone: Asia/Tehran
- Calendar: Jalali (Shamsi)
- Day names in Persian

**Key Functions**:
- `get_current_time_iran()`: Now in Iran TZ
- `get_today_gregorian()`: Today's Gregorian date
- `gregorian_to_jalali()`: Convert to Jalali tuple
- `jalali_to_gregorian()`: Convert to Gregorian
- `gregorian_to_jalali_str()`: Format as "YYYY/MM/DD"
- `format_date_persian()`: Format with day name
- `get_week_start_end()`: Week boundaries
- `get_month_start_end()`: Month boundaries

**Conversion Example**:
```
2024-04-27 (Gregorian)
    ↓ gregorian_to_jalali()
1405/02/07 (Jalali)
    ↓ get_jalali_day_name()
شنبه (Saturday in Persian)
    ↓ format_date_persian()
"شنبه 1405/02/07"
```

#### `utils/formatter.py` - Message Formatter
**Purpose**: Format messages for Bale in Persian  
**Message Types**:
- Daily reports
- Weekly/monthly summaries
- Admin reports
- Penalty notifications
- User profiles

**Key Classes**:
- `MessageFormatter`: Static methods for formatting

**Examples**:
```python
# Daily report
msg = MessageFormatter.format_daily_report_group(
    user_name="Amir",
    main_hours=6,
    side_hours=2,
    total_hours=8,
    report_date=date(2024, 4, 27)
)
# Output:
# 👤 Amir
# 📌 اصلی: 6
# 📌 فرعی: 2
# ➕ مجموع: 8
# 📅 شنبه 1405/02/07
```

## 🔄 Data Flow Examples

### Example 1: Daily Report Submission

```
┌─────────────────────────────────────────────────────────┐
│ User clicks "📊 ثبت گزارش روزانه"                      │
└────────────────┬────────────────────────────────────────┘
                 │
        Message arrives at bot
                 │
         _handle_callback_query()
                 │
    data == "daily_report"
                 │
   TaskHandler.handle_daily_report_start()
                 │
    Check user registration (via database.get_user_by_bale_id)
                 │
    Show today's date (via date_utils.format_date_persian)
                 │
    Save state: waiting_main_hours
                 │
    Prompt: "ساعت کاری اصلی را وارد کن"
                 │
        ┌────────────────────────────────┐
        │ User enters "6.5"              │
        └────────────┬───────────────────┘
                     │
         _handle_message() with state
                     │
      TaskHandler.handle_main_hours_input()
                     │
      Validate: 0 <= 6.5 <= 12 ✅
                     │
      Update state: waiting_side_hours
                     │
      Prompt: "ساعت کاری فرعی را وارد کن"
                     │
        ┌────────────────────────────────┐
        │ User enters "2"                │
        └────────────┬───────────────────┘
                     │
      TaskHandler.handle_side_hours_input()
                     │
      Validate: 0 <= 2 <= 8 ✅
                     │
      ReportService.submit_daily_report()
                     │
      ├─ Check: report doesn't exist
      ├─ Database.report_exists() → False ✅
      ├─ Create Report object
      ├─ Database.add_report()
      │
      └─ Success!
                     │
      Send confirmation to user
      Send notification to group
                     │
       ┌─────────────────────────────────┐
       │ ✅ گزارش ثبت شد               │
       │ 👤 Amir                         │
       │ ⬛️ اصلی: 6.5                   │
       │ 🔵 فرعی: 2                     │
       │ ➕ مجموع: 8.5                  │
       └─────────────────────────────────┘
```

### Example 2: Penalty Check (Scheduled Daily)

```
APScheduler triggers at 10:00 AM (Iran time)
                 │
    _check_missing_reports()
                 │
   date = yesterday (2024-04-26)
                 │
   Database.get_missing_report_users("2024-04-26")
                 │
   Returns: [(2, "Ahmad"), (5, "Sara"), ...]
                 │
   For each user without report:
                 │
   ├─ Check if penalty already exists
   │
   └─ PenaltyService.check_and_create_missing_report_penalties()
                 │
      ├─ Create Penalty object
      ├─ Database.add_penalty()
      └─ PenaltyService returns created penalties
                 │
   Notify each user:
   "⚠️ گزارش روز 1405/02/06 را ثبت نکردید"
                 │
   Log: "Penalties created: 2"
```

### Example 3: Admin Weekly Report

```
Admin sends /admin
                 │
       AdminHandler.handle_admin_panel()
                 │
   ├─ check_admin_permission() → True ✅
   │
   └─ Show admin menu
                 │
   Admin clicks "📊 گزارش هفتگی"
                 │
   AdminHandler.handle_weekly_report_admin()
                 │
   ReportService.get_all_weekly_stats()
                 │
   ├─ For each user:
   │  ├─ get_week_start_end()
   │  └─ get_reports_by_user_and_date()
   │      └─ Sum hours for week
   │
   └─ Returns: [(stats1, "user1"), (stats2, "user2"), ...]
                 │
   MessageFormatter.format_admin_weekly_summary()
                 │
   ├─ Extract week dates
   ├─ Calculate totals
   └─ Format Persian message
                 │
   Send summary to admin:
   ┌──────────────────────────────┐
   │ 📊 خلاصه هفتگی               │
   │ 1405/02/01 تا 1405/02/07    │
   │ ═════════════════════════    │
   │ Amir: 42h (35+7)            │
   │ Ahmad: 38h (30+8)           │
   │ Sara: 40h (32+8)            │
   │ ═════════════════════════    │
   │ 👥 کل کاربران: 3            │
   │ ⬛️ کل اصلی: 97              │
   │ 🔵 کل فرعی: 23              │
   │ 📈 کل کل: 120               │
   │ 📊 میانگین: 40.0            │
   └──────────────────────────────┘
```

## 🔐 Security Considerations

### 1. Admin Authorization
```python
def check_admin_permission(user_id: int) -> bool:
    return user_id in BALE_ADMIN_IDS
```
- Only admin IDs from config allowed
- Checked for every admin action
- Prevents unauthorized access

### 2. User Privacy
- Phone numbers: Only visible to user
- Bios: Visible to all
- Reports: Personal data stored safely
- Penalties: Private between user and admin

### 3. Data Validation
- Hours: 0-12 for main, 0-8 for side
- Names: Minimum 2 characters
- Dates: No duplicate reports per day
- Penalties: Can only be created once per date

### 4. Database Safety
- Foreign key constraints
- Unique constraints on (user_id, date)
- Proper transaction handling
- Error logging for debugging

## 📊 Performance Notes

### Database Performance
- **Small teams (< 100)**: No optimization needed
- **Medium teams (100-500)**: Add indexes on frequently queried columns
- **Large teams (> 500)**: Consider PostgreSQL migration

### Scheduler Performance
- Single background thread
- APScheduler is lightweight
- No blocking operations
- Graceful handling of clock changes

### Message Handling
- Async message processing
- Quick response time (< 1 second)
- Proper error handling
- Logging for debugging

## 🚀 Extensibility

### Adding New Features

1. **New Handler**: Create in `handlers/newfeature.py`
   - Inherit patterns from existing handlers
   - Implement state machine if needed
   - Register in bot.py

2. **New Service**: Create in `services/newservice.py`
   - Handle business logic
   - Use Database for persistence
   - Use models for data structures

3. **New Database Table**: Add to `config/settings.py`
   - Define schema in DATABASE_SCHEMA
   - Add CRUD methods to `database/db.py`
   - Create corresponding model

4. **New Report Type**: Extend `ReportService`
   - Add calculation method
   - Add formatting in `formatter.py`
   - Wire up in handler

## 📈 Monitoring & Debugging

### Log Levels
```python
logger.debug()    # Detailed info for developers
logger.info()     # General information
logger.warning()  # Potential issues
logger.error()    # Errors that need attention
logger.critical() # System failure
```

### Enable Debug Logging
In `config/settings.py`:
```python
LOG_LEVEL = "DEBUG"  # Shows all debug messages
```

### Database Inspection
```bash
sqlite3 data/database.db

# Check tables
.tables
.schema users

# View data
SELECT COUNT(*) FROM users;
SELECT * FROM reports WHERE date_gregorian = '2024-04-27';
SELECT * FROM penalties WHERE status = 'unpaid';
```

---

**Architecture Version**: 1.0  
**Last Updated**: April 2026  
**Status**: Production Ready ✅
