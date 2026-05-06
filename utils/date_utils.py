"""
Date utility module for timezone and Jalali calendar conversions.
Uses jdatetime library for accurate Gregorian <-> Jalali conversion.
"""

import datetime
from typing import Tuple
import pytz
import jdatetime
from dateutil.relativedelta import relativedelta

# Iran timezone
IRAN_TZ = pytz.timezone("Asia/Tehran")


def get_current_time_iran() -> datetime.datetime:
    """Get current datetime in Iran timezone."""
    return datetime.datetime.now(IRAN_TZ)


def get_today_gregorian() -> datetime.date:
    """Get today's date (Gregorian) based on Iran timezone."""
    return get_current_time_iran().date()


def get_now_time_str() -> str:
    """
    Get current Iran time as HH:MM string.
    Example: '14:35'
    """
    now = get_current_time_iran()
    return now.strftime("%H:%M")


def gregorian_to_jalali(gregorian_date: datetime.date) -> Tuple[int, int, int]:
    """
    Convert Gregorian date to Jalali (Shamsi) using jdatetime.

    Returns:
        Tuple[int, int, int]: (year, month, day)
    """
    jd = jdatetime.date.fromgregorian(date=gregorian_date)
    return jd.year, jd.month, jd.day


def jalali_to_gregorian(jy: int, jm: int, jd: int) -> datetime.date:
    """Convert Jalali date to Gregorian."""
    return jdatetime.date(jy, jm, jd).togregorian()


def gregorian_to_jalali_str(gregorian_date: datetime.date) -> str:
    """
    Convert Gregorian date to Jalali string 'YYYY/MM/DD'.
    Example: '1405/02/16'
    """
    jy, jm, jd = gregorian_to_jalali(gregorian_date)
    return f"{jy:04d}/{jm:02d}/{jd:02d}"


def get_jalali_today_str() -> str:
    """Today's date as Jalali string."""
    return gregorian_to_jalali_str(get_today_gregorian())


def get_jalali_day_name(gregorian_date: datetime.date) -> str:
    """
    Return Persian weekday name for a Gregorian date.
    Iran week: Saturday=0 ... Friday=6
    Python weekday(): Monday=0 ... Sunday=6
    """
    # Map Python weekday to Persian name
    day_map = {
        5: "شنبه",
        6: "یکشنبه",
        0: "دوشنبه",
        1: "سه‌شنبه",
        2: "چهارشنبه",
        3: "پنج‌شنبه",
        4: "جمعه",
    }
    return day_map.get(gregorian_date.weekday(), "نامشخص")


def format_date_persian(gregorian_date: datetime.date) -> str:
    """
    Format as 'روز YYYY/MM/DD'.
    Example: 'دوشنبه ۱۴۰۵/۰۲/۱۶'
    """
    jalali_str = gregorian_to_jalali_str(gregorian_date)
    day_name = get_jalali_day_name(gregorian_date)
    return f"{day_name} {jalali_str}"


def format_datetime_persian(dt: datetime.datetime = None) -> str:
    """
    Format a datetime as 'روز YYYY/MM/DD ساعت HH:MM' in Iran time.
    If dt is None, uses current Iran time.
    Example: 'دوشنبه ۱۴۰۵/۰۲/۱۶  ساعت ۱۴:۳۵'
    """
    if dt is None:
        dt = get_current_time_iran()
    elif dt.tzinfo is None:
        # Assume UTC if no timezone, convert to Iran
        dt = pytz.utc.localize(dt).astimezone(IRAN_TZ)
    else:
        dt = dt.astimezone(IRAN_TZ)

    date_str = format_date_persian(dt.date())
    time_str = dt.strftime("%H:%M")
    return f"{date_str}  ساعت {time_str}"


def format_date_range_persian(start_date: datetime.date, end_date: datetime.date) -> str:
    """Format a date range in Persian."""
    return f"{gregorian_to_jalali_str(start_date)} تا {gregorian_to_jalali_str(end_date)}"


def get_week_start_end() -> Tuple[datetime.date, datetime.date]:
    """
    Current week bounds (Saturday–Friday, Iran calendar).
    """
    today = get_today_gregorian()
    # Saturday = weekday 5 in Python
    days_since_saturday = (today.weekday() - 5) % 7
    week_start = today - datetime.timedelta(days=days_since_saturday)
    week_end = week_start + datetime.timedelta(days=6)
    return week_start, week_end


def get_month_start_end() -> Tuple[datetime.date, datetime.date]:
    """Current Gregorian month start and end."""
    today = get_today_gregorian()
    month_start = today.replace(day=1)
    month_end = (month_start + relativedelta(months=1)) - datetime.timedelta(days=1)
    return month_start, month_end


def get_yesterday() -> datetime.date:
    """Yesterday's date in Iran timezone."""
    return get_today_gregorian() - datetime.timedelta(days=1)


def is_leap_gregorian(year: int) -> bool:
    return (year % 4 == 0 and year % 100 != 0) or (year % 400 == 0)


def is_leap_jalali(year: int) -> bool:
    return jdatetime.date(year, 1, 1).isleap()
