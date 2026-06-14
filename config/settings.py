"""
Configuration module for EliteUniteTime bot system.
Contains all settings, environment variables, and constants.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Project root directory
BASE_DIR = Path(__file__).parent.parent

# ======================
# BALE BOT CONFIGURATION
# ======================
BALE_API_TOKEN = os.getenv("BALE_API_TOKEN", "")


def _parse_int_list(raw: str) -> list[int]:
    """Parse comma-separated integer IDs from env (empty/placeholder → [])."""
    if not raw or raw.strip() in ("", "your_group_id_here"):
        return []
    return [int(item.strip()) for item in raw.split(",") if item.strip()]


# One or more group chat IDs (comma-separated in .env)
BALE_GROUP_IDS = _parse_int_list(os.getenv("BALE_GROUP_ID", ""))
BALE_ADMIN_IDS = _parse_int_list(os.getenv("BALE_ADMIN_IDS", "0")) or [0]

# ======================
# TIMEZONE CONFIGURATION
# ======================
# Iran timezone for all time operations
TIMEZONE = "Asia/Tehran"

# ======================
# DATABASE CONFIGURATION
# ======================
DATABASE_PATH = BASE_DIR / "data" / "database.db"
DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)

# ======================
# SCHEDULER CONFIGURATION
# ======================
# Time to check for missing reports (10 AM Iran time)
MISSING_REPORT_CHECK_HOUR = 10
MISSING_REPORT_CHECK_MINUTE = 0

# Penalty amount for missing daily report
PENALTY_AMOUNT = 1  # Penalty points

# ======================
# REPORT CONFIGURATION
# ======================
# Maximum hours per day allowed
MAX_MAIN_HOURS = 12
MAX_SIDE_HOURS = 8
MAX_TOTAL_HOURS = 20

# ======================
# MESSAGE TEMPLATES
# ======================
MESSAGES = {
    "welcome": "خوش آمدید به سیستم مدیریت زمان EliteUniteTime\n\nلطفاً اطلاعات خود را کامل کنید",
    "enter_name": "لطفاً نام کامل خود را وارد کنید:",
    "enter_phone": "لطفاً شماره تماس خود را ارسال کنید:",
    "registration_complete": "ثبت نام شما با موفقیت انجام شد! 🎉",
    "today_date": "امروز: {day_name} {date_shamsi}",
    "enter_main_hours": "ساعت کاری اصلی را وارد کن:",
    "enter_side_hours": "ساعت کاری فرعی را وارد کن:",
    "report_saved": "گزارش شما با موفقیت ثبت شد! ✅",
    "missing_report": "گزارش روز {date_shamsi} را ثبت نکردید",
    "penalty_created": "مجازات ایجاد شد: {reason}",
}

# ======================
# BUTTON LABELS
# ======================
BUTTON_LABELS = {
    "daily_report": "📊 ثبت گزارش روزانه",
    "weekly_report": "📈 گزارش هفتگی",
    "monthly_report": "📅 گزارش ماهانه",
    "profile": "👤 پروفایل من",
    "friends": "👥 آشنایی با دوستان",
    "admin": "⚙️ پنل ادمین",
    "share_contact": "📞 اشتراک گذاری شماره",
}

# ======================
# DATABASE TABLES SCHEMA
# ======================
DATABASE_SCHEMA = {
    "users": """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            bale_id INTEGER UNIQUE NOT NULL,
            full_name TEXT NOT NULL,
            phone TEXT,
            bio TEXT DEFAULT '',
            interests TEXT DEFAULT '',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """,
    "reports": """
        CREATE TABLE IF NOT EXISTS reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            date_shamsi TEXT NOT NULL,
            date_gregorian TEXT NOT NULL,
            main_hours REAL DEFAULT 0,
            side_hours REAL DEFAULT 0,
            total_hours REAL DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id),
            UNIQUE(user_id, date_gregorian)
        )
    """,
    "penalties": """
        CREATE TABLE IF NOT EXISTS penalties (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            date_shamsi TEXT NOT NULL,
            date_gregorian TEXT NOT NULL,
            amount INTEGER DEFAULT 1,
            reason TEXT NOT NULL,
            status TEXT DEFAULT 'unpaid',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    """,
}
