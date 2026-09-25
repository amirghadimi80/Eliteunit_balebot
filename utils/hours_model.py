"""
Hours reporting model helpers.

Until 1405/07/03: main + side (additive) → total
From 1405/07/04 (Saturday): useful hours + growth hours (subset, not summed)
"""

from __future__ import annotations

from datetime import date
from typing import Union

from utils.date_utils import jalali_to_gregorian

# شنبه ۴ مهر ۱۴۰۵ — شروع مدل جدید ساعت‌زنی
HOURS_V2_START: date = jalali_to_gregorian(1405, 7, 4)

# حدود مجاز
MAX_MAIN_HOURS_V1 = 12
MAX_SIDE_HOURS_V1 = 8
MAX_USEFUL_HOURS_V2 = 20  # کل ساعت مفید روز


DateLike = Union[date, str, None]


def _as_date(value: DateLike) -> date:
    if value is None:
        return date.min
    if isinstance(value, date):
        return value
    text = str(value).strip()
    if "/" in text and text.count("/") == 2:
        # Jalali YYYY/MM/DD — only used if caller passes shamsi by mistake
        parts = text.split("/")
        if len(parts[0]) == 4:
            from utils.date_utils import jalali_to_gregorian as j2g
            return j2g(int(parts[0]), int(parts[1]), int(parts[2]))
    return date.fromisoformat(text[:10])


def uses_v2_hours(report_date: DateLike) -> bool:
    """True from 4 Mehr 1405 onward (growth subset model)."""
    return _as_date(report_date) >= HOURS_V2_START


def period_uses_v2(start: DateLike, end: DateLike = None) -> bool:
    """Prefer v2 labels if the period includes any day on/after the cutoff."""
    end_date = _as_date(end) if end is not None else _as_date(start)
    return end_date >= HOURS_V2_START


def compute_total_hours(main_hours: float, side_hours: float, report_date: DateLike) -> float:
    """
    V1: main + side
    V2: total = useful (main) only — growth is a subset, not added
    """
    if uses_v2_hours(report_date):
        return float(main_hours or 0)
    return float(main_hours or 0) + float(side_hours or 0)


def growth_percent(useful_hours: float, growth_hours: float) -> int:
    """Growth as percent of useful hours (0–100)."""
    useful = float(useful_hours or 0)
    growth = float(growth_hours or 0)
    if useful <= 0:
        return 0
    return int(round((growth / useful) * 100))


def labels_for(report_date: DateLike) -> dict:
    """Persian field labels for the given report date."""
    if uses_v2_hours(report_date):
        return {
            "first": "کل ساعت مفید",
            "second": "ساعت رشد",
            "first_short": "مفید",
            "second_short": "رشد",
            "total": "کل ساعت مفید",
            "prompt_first": (
                "⬛️ کل ساعت مفید روز را وارد کنید:\n"
                "(کار، ورزش، کتاب، دوره، مطالعه، پادکست و ...)\n"
                "سنجش اراده و بهره‌وری\n\n"
                "(مثال: 10 یا 6:30)"
            ),
            "prompt_second": (
                "🟢 ساعت رشد را وارد کنید:\n"
                "(بخشی از ساعات مفید که در راستای اهداف شخصی بوده)\n"
                "سنجش بازدهی و پیشرفت فردی\n\n"
                "⚠️ این عدد نباید از کل ساعت مفید بیشتر باشد.\n"
                "(مثال: 2 یا 1:30)"
            ),
            "max_first": MAX_USEFUL_HOURS_V2,
            "max_second": MAX_USEFUL_HOURS_V2,
        }
    return {
        "first": "ساعت اصلی",
        "second": "ساعت فرعی",
        "first_short": "اصلی",
        "second_short": "فرعی",
        "total": "مجموع",
        "prompt_first": (
            "⬛️ لطفاً ساعت کاری اصلی را وارد کنید:\n"
            "(مثال: 6 یا 2:30)"
        ),
        "prompt_second": (
            "🔵 لطفاً ساعت کاری فرعی را وارد کنید:\n"
            "(ورزش، پادکست، یادگیری، ...)\n\n"
            "(مثال: 2 یا 0:30)"
        ),
        "max_first": MAX_MAIN_HOURS_V1,
        "max_second": MAX_SIDE_HOURS_V1,
    }


def validate_hours(
    main_hours: float,
    side_hours: float,
    report_date: DateLike,
) -> tuple[bool, str]:
    """Validate hours for the active model. Returns (ok, error_message)."""
    if main_hours < 0 or side_hours < 0:
        return False, "ساعات نمی‌تواند منفی باشند"

    if uses_v2_hours(report_date):
        if main_hours > MAX_USEFUL_HOURS_V2:
            return False, f"کل ساعت مفید نمی‌تواند بیشتر از {MAX_USEFUL_HOURS_V2} باشد"
        if side_hours > main_hours:
            return False, "ساعت رشد نمی‌تواند از کل ساعت مفید بیشتر باشد"
        return True, ""

    if main_hours > MAX_MAIN_HOURS_V1:
        return False, f"ساعات اصلی باید بین 0 تا {MAX_MAIN_HOURS_V1} باشد"
    if side_hours > MAX_SIDE_HOURS_V1:
        return False, f"ساعات فرعی باید بین 0 تا {MAX_SIDE_HOURS_V1} باشد"
    return True, ""
