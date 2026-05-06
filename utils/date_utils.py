"""
Date utility module for timezone and Jalali calendar conversions.
Handles Iran timezone (Asia/Tehran) and Gregorian-Jalali conversions.
"""

import datetime
from typing import Tuple, Dict
import pytz
from dateutil.relativedelta import relativedelta

# Iran timezone
IRAN_TZ = pytz.timezone("Asia/Tehran")


def get_current_time_iran() -> datetime.datetime:
    """
    Get current time in Iran timezone (Asia/Tehran).
    
    Returns:
        datetime.datetime: Current time in Iran timezone with timezone info
    """
    return datetime.datetime.now(IRAN_TZ)


def get_today_gregorian() -> datetime.date:
    """
    Get today's date in Gregorian calendar (Iran timezone).
    
    Returns:
        datetime.date: Today's date in Gregorian calendar
    """
    return get_current_time_iran().date()


def gregorian_to_jalali(gregorian_date: datetime.date) -> Tuple[int, int, int]:
    """
    Convert Gregorian date to Jalali (Shamsi) calendar.
    Uses Wikipedia algorithm for accurate conversion.
    
    Args:
        gregorian_date: Date in Gregorian calendar
        
    Returns:
        Tuple[int, int, int]: (year, month, day) in Jalali calendar
    """
    gy, gm, gd = gregorian_date.year, gregorian_date.month, gregorian_date.day
    
    # Algorithm to convert Gregorian to Jalali
    if gm > 2:
        gy2 = gy + 1
    else:
        gy2 = gy
    
    days = (365 * gy) + ((gy2 + 3) // 4) - ((gy2 + 99) // 100) + ((gy2 + 399) // 400)
    days += gd
    
    for i in range(1, gm):
        if gm > 2 and i == 2:
            days += 29 if is_leap_gregorian(gy) else 28
        elif i in [4, 6, 9, 11]:
            days += 30
        else:
            days += 31
    
    jy = -1595 + 33 * ((days // 146097) * 400 + (days % 146097) // 36524)
    days %= 36524
    
    jy += 4 * ((days // 1461) * 4 + (days % 1461) // 365) - (days % 1461) // 365 + 1
    days %= 1461
    
    jy += ((days // 365) * 365 + (days % 365)) // 365
    days = ((days // 365) * 365 + (days % 365)) % 365
    
    if days < 186:
        jm = 1 + days // 31
        jd = 1 + (days % 31)
    else:
        jm = 7 + (days - 186) // 30
        jd = 1 + ((days - 186) % 30)
    
    return jy, jm, jd


def jalali_to_gregorian(jy: int, jm: int, jd: int) -> datetime.date:
    """
    Convert Jalali (Shamsi) date to Gregorian calendar.
    
    Args:
        jy: Jalali year
        jm: Jalali month (1-12)
        jd: Jalali day (1-31)
        
    Returns:
        datetime.date: Date in Gregorian calendar
    """
    jy += 1474
    if jy <= 0:
        jy -= 1
    
    doy = 365 * jy + (jy // 33) * 8 + ((jy % 33 + 3) // 4) + 78 + jd
    
    if jm < 7:
        doy += (jm - 1) * 31
    else:
        doy += (jm - 7) * 30 + 186
    
    gy = 400 * (doy // 146097)
    doy %= 146097
    
    flag = True
    if doy >= 36525:
        doy -= 1
        gy += 100 * (doy // 36524)
        doy %= 36524
        if doy >= 365:
            doy += 1
        flag = False
    
    gy += 4 * (doy // 1461)
    doy %= 1461
    
    if flag:
        if doy >= 366:
            doy -= 1
            gy += doy // 365
            doy = doy % 365
    
    return datetime.date(gy, 1, 1) + datetime.timedelta(days=doy)


def is_leap_gregorian(year: int) -> bool:
    """
    Check if a year is leap in Gregorian calendar.
    
    Args:
        year: Year to check
        
    Returns:
        bool: True if leap year, False otherwise
    """
    return (year % 4 == 0 and year % 100 != 0) or (year % 400 == 0)


def is_leap_jalali(year: int) -> bool:
    """
    Check if a year is leap in Jalali calendar.
    
    Args:
        year: Jalali year to check
        
    Returns:
        bool: True if leap year, False otherwise
    """
    cycle = year + 1474
    if cycle < 0:
        cycle += 1
    return (cycle % 2820 + 474) * 682 % 2816 < 682


def gregorian_to_jalali_str(gregorian_date: datetime.date) -> str:
    """
    Convert Gregorian date to Jalali string format (YYYY/MM/DD).
    
    Args:
        gregorian_date: Date in Gregorian calendar
        
    Returns:
        str: Date in format "YYYY/MM/DD"
    """
    jy, jm, jd = gregorian_to_jalali(gregorian_date)
    return f"{jy:04d}/{jm:02d}/{jd:02d}"


def get_jalali_today_str() -> str:
    """
    Get today's date as Jalali string (YYYY/MM/DD).
    
    Returns:
        str: Today's Jalali date in format "YYYY/MM/DD"
    """
    return gregorian_to_jalali_str(get_today_gregorian())


def get_jalali_day_name(gregorian_date: datetime.date) -> str:
    """
    Get Persian day name for a given date.
    
    Args:
        gregorian_date: Date in Gregorian calendar
        
    Returns:
        str: Persian day name
    """
    day_names = {
        0: "شنبه",      # Saturday
        1: "یکشنبه",    # Sunday
        2: "دوشنبه",    # Monday
        3: "سه‌شنبه",   # Tuesday
        4: "چهارشنبه",  # Wednesday
        5: "پنج‌شنبه",  # Thursday
        6: "جمعه",      # Friday
    }
    return day_names.get(gregorian_date.weekday(), "نامشخص")


def format_date_persian(gregorian_date: datetime.date) -> str:
    """
    Format date as Persian string with day name and date.
    Example: "دوشنبه 1405/02/07"
    
    Args:
        gregorian_date: Date in Gregorian calendar
        
    Returns:
        str: Formatted Persian date string
    """
    jalali_str = gregorian_to_jalali_str(gregorian_date)
    day_name = get_jalali_day_name(gregorian_date)
    return f"{day_name} {jalali_str}"


def format_date_range_persian(start_date: datetime.date, end_date: datetime.date) -> str:
    """
    Format a date range in Persian format.
    
    Args:
        start_date: Start date in Gregorian calendar
        end_date: End date in Gregorian calendar
        
    Returns:
        str: Formatted date range
    """
    start_jalali = gregorian_to_jalali_str(start_date)
    end_jalali = gregorian_to_jalali_str(end_date)
    return f"{start_jalali} تا {end_jalali}"


def get_week_start_end() -> Tuple[datetime.date, datetime.date]:
    """
    Get start and end dates of current week (Saturday to Friday in Iran).
    
    Returns:
        Tuple[datetime.date, datetime.date]: (week_start, week_end)
    """
    today = get_today_gregorian()
    # In Iran, week starts on Saturday (weekday 5)
    week_start = today - datetime.timedelta(days=(today.weekday() - 5) % 7)
    week_end = week_start + datetime.timedelta(days=6)
    return week_start, week_end


def get_month_start_end() -> Tuple[datetime.date, datetime.date]:
    """
    Get start and end dates of current month.
    
    Returns:
        Tuple[datetime.date, datetime.date]: (month_start, month_end)
    """
    today = get_today_gregorian()
    month_start = today.replace(day=1)
    month_end = (month_start + relativedelta(months=1)) - datetime.timedelta(days=1)
    return month_start, month_end


def get_yesterday() -> datetime.date:
    """
    Get yesterday's date in Gregorian calendar.
    
    Returns:
        datetime.date: Yesterday's date
    """
    return get_today_gregorian() - datetime.timedelta(days=1)
