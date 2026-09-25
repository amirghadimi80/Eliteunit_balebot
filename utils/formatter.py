"""
Message formatting utility module.
Contains functions to format messages, reports, and group notifications.
"""

from typing import List, Dict, Optional
from datetime import datetime, date
from config.settings import PAYMENT_CARD_NUMBER, PAYMENT_CARD_HOLDER
from utils.date_utils import (
    gregorian_to_jalali_str,
    get_jalali_day_name,
    format_date_persian,
)
from utils.time_utils import format_duration
from utils.hours_model import (
    uses_v2_hours,
    period_uses_v2,
    growth_percent,
    labels_for,
    compute_total_hours,
    HOURS_V2_START,
)


class MessageFormatter:
    """Utility class for formatting messages in Persian."""
    
    @staticmethod
    def format_daily_report_group(
        user_name: str,
        main_hours: float,
        side_hours: float,
        total_hours: float,
        report_date: date,
        submit_time: str = "",
        is_late: bool = False,
    ) -> str:
        """
        Format a daily report message for group notification.

        From 1405/07/04: useful + growth + growth percent (no sum).
        Before that: main + side + total.
        """
        date_str = format_date_persian(report_date)
        time_part = f"  🕐 {submit_time}" if submit_time else ""
        header = "📋 گزارش معوقه\n" if is_late else ""
        labels = labels_for(report_date)

        if uses_v2_hours(report_date):
            pct = growth_percent(main_hours, side_hours)
            message = (
                f"{header}"
                f"👤 {user_name}\n"
                f"📌 {labels['first']}: {format_duration(main_hours)}\n"
                f"📌 {labels['second']}: {format_duration(side_hours)}\n"
                f"📈 درصد رشد از ساعت کار: {pct} درصد\n"
                f"📅 {date_str}{time_part}"
            )
        else:
            total = compute_total_hours(main_hours, side_hours, report_date)
            message = (
                f"{header}"
                f"👤 {user_name}\n"
                f"📌 {labels['first_short']}: {format_duration(main_hours)}\n"
                f"📌 {labels['second_short']}: {format_duration(side_hours)}\n"
                f"➕ مجموع: {format_duration(total)}\n"
                f"📅 {date_str}{time_part}"
            )
        return message
    
    @staticmethod
    def format_daily_summary_group(reports: List[Dict]) -> str:
        """
        Format a group summary with all users' reports for the day.
        
        Args:
            reports: List of report dictionaries with keys:
                    - user_name, main_hours, side_hours, total_hours, report_date
                    
        Returns:
            str: Formatted group summary
        """
        if not reports:
            return "❌ هیچ گزارشی امروز ثبت نشده است"
        
        report_date = reports[0].get("report_date") if reports else None
        date_str = format_date_persian(report_date) if report_date else "نامشخص"
        labels = labels_for(report_date)
        v2 = uses_v2_hours(report_date)
        
        message = f"📊 خلاصه روزانه - {date_str}\n{'=' * 40}\n"
        
        total_main = 0
        total_side = 0
        total_all = 0
        
        for report in reports:
            main = report.get("main_hours", 0)
            side = report.get("side_hours", 0)
            rdate = report.get("report_date", report_date)
            total = compute_total_hours(main, side, rdate)
            
            if v2:
                pct = growth_percent(main, side)
                message += (
                    f"👤 {report.get('user_name', 'نامشخص')}: "
                    f"{format_duration(main)} مفید · "
                    f"{format_duration(side)} رشد ({pct}%)\n"
                )
            else:
                message += (
                    f"👤 {report.get('user_name', 'نامشخص')}: "
                    f"{format_duration(total)} "
                    f"(⬛️{format_duration(main)} + 🔵{format_duration(side)})\n"
                )
            
            total_main += main
            total_side += side
            total_all += total
        
        message += f"\n{'=' * 40}\n"
        if v2:
            pct = growth_percent(total_main, total_side)
            message += (
                f"📈 کل {labels['first']}: {format_duration(total_main)}\n"
                f"🟢 کل {labels['second']}: {format_duration(total_side)}\n"
                f"📊 درصد رشد از ساعت کار: {pct} درصد"
            )
        else:
            message += (
                f"📈 کل: {format_duration(total_all)}\n"
                f"⬛️ اصلی: {format_duration(total_main)} | 🔵 فرعی: {format_duration(total_side)}"
            )
        
        return message
    
    @staticmethod
    def format_weekly_report(
        user_name: str,
        week_start: date,
        week_end: date,
        main_hours: float,
        side_hours: float,
        total_hours: float,
    ) -> str:
        """Format a weekly report for a user."""
        date_range = f"{gregorian_to_jalali_str(week_start)} تا {gregorian_to_jalali_str(week_end)}"
        labels = labels_for(week_end if period_uses_v2(week_start, week_end) else week_start)

        if period_uses_v2(week_start, week_end):
            pct = growth_percent(main_hours, side_hours)
            message = (
                f"📈 گزارش هفتگی\n"
                f"👤 {user_name}\n"
                f"📅 {date_range}\n\n"
                f"⬛️ {labels['first']}: {format_duration(main_hours)}\n"
                f"🟢 {labels['second']}: {format_duration(side_hours)}\n"
                f"📈 درصد رشد از ساعت کار: {pct} درصد"
            )
        else:
            message = (
                f"📈 گزارش هفتگی\n"
                f"👤 {user_name}\n"
                f"📅 {date_range}\n\n"
                f"⬛️ ساعت اصلی: {format_duration(main_hours)}\n"
                f"🔵 ساعت فرعی: {format_duration(side_hours)}\n"
                f"➕ مجموع: {format_duration(total_hours)}"
            )
        return message
    
    @staticmethod
    def format_monthly_report(
        user_name: str,
        year: int,
        month: int,
        main_hours: float,
        side_hours: float,
        total_hours: float,
        days_reported: int,
        days_total: int,
        month_end: date = None,
    ) -> str:
        """Format a monthly report for a user."""
        # Prefer v2 labels once the month reaches/passes 4 Mehr 1405
        use_v2 = False
        if month_end is not None:
            use_v2 = period_uses_v2(month_end, month_end)
        elif year > 1405 or (year == 1405 and month >= 7):
            use_v2 = True

        if use_v2:
            labels = labels_for(HOURS_V2_START)
            pct = growth_percent(main_hours, side_hours)
            message = (
                f"📅 گزارش ماهانه\n"
                f"👤 {user_name}\n"
                f"🗓️  {year:04d}/{month:02d}\n\n"
                f"⬛️ {labels['first']}: {format_duration(main_hours)}\n"
                f"🟢 {labels['second']}: {format_duration(side_hours)}\n"
                f"📈 درصد رشد از ساعت کار: {pct} درصد\n\n"
                f"📊 روزهای ثبت شده: {days_reported}/{days_total}"
            )
        else:
            message = (
                f"📅 گزارش ماهانه\n"
                f"👤 {user_name}\n"
                f"🗓️  {year:04d}/{month:02d}\n\n"
                f"⬛️ ساعت اصلی: {format_duration(main_hours)}\n"
                f"🔵 ساعت فرعی: {format_duration(side_hours)}\n"
                f"➕ مجموع: {format_duration(total_hours)}\n\n"
                f"📊 روزهای ثبت شده: {days_reported}/{days_total}"
            )
        return message
    
    @staticmethod
    def format_penalty_notification(
        user_name: str,
        missing_dates: List[str],
    ) -> str:
        """
        Format a penalty notification message for missing reports.
        
        Args:
            user_name: User's full name
            missing_dates: List of missing dates in Jalali format
            
        Returns:
            str: Formatted penalty notification
        """
        if not missing_dates:
            return "هیچ گزارش کمی وجود ندارد"
        
        message = f"⚠️ جریمه برای {user_name}\n\n"
        message += "روزهای ثبت نشده:\n"
        
        for date in missing_dates:
            message += f"❌ {date}\n"
        
        message += f"\nکل جریمه‌ها: {len(missing_dates)}"
        
        return message

    @staticmethod
    def _payment_block() -> str:
        return (
            f"سریع واریز کنید به کارت:\n"
            f"💳 {PAYMENT_CARD_NUMBER}\n"
            f"به نام {PAYMENT_CARD_HOLDER}"
        )

    @staticmethod
    def format_bot_report_action(date_shamsi: str) -> str:
        return (
            f"📝 الان برو توی بات و گزارش روز {date_shamsi} را وارد کن:\n"
            f"منو → 📊 ثبت گزارش روزانه\n\n"
            f"⚠️ ابتدا همه روزهای قبلی که ثبت نشده را وارد کن، بعد گزارش امروز."
        )

    @staticmethod
    def _bot_report_reminder() -> str:
        return (
            "📝 گزارش را داخل بات ثبت کنید:\n"
            "منو → 📊 ثبت گزارش روزانه\n\n"
            "⚠️ ابتدا روزهای قبلی که ثبت نشده را وارد کن، بعد گزارش امروز."
        )

    @staticmethod
    def format_penalty_user_message(
        user_name: str,
        amount: int,
        date_shamsi: str,
    ) -> str:
        """Private message to penalized user."""
        return (
            f"⚠️ {user_name} عزیز\n\n"
            f"شما {amount:,} تومان جریمه شدید.\n"
            f"گزارش روز {date_shamsi} ثبت نشده.\n"
            f"مهلت: تا ساعت ۱۰ صبح روز بعد.\n\n"
            f"{MessageFormatter.format_bot_report_action(date_shamsi)}\n\n"
            f"{MessageFormatter._payment_block()}"
        )

    @staticmethod
    def format_penalty_group_message(
        user_name: str,
        amount: int,
        date_shamsi: str,
    ) -> str:
        """Group announcement for a new penalty."""
        return (
            f"⚠️ {user_name} — {amount:,} تومان جریمه شد\n"
            f"گزارش روز {date_shamsi} ثبت نشده.\n\n"
            f"{MessageFormatter.format_bot_report_action(date_shamsi)}\n\n"
            f"{MessageFormatter._payment_block()}"
        )

    @staticmethod
    def format_penalty_paid_message(user_name: str, amount: int, days_count: int = 1) -> str:
        """Notification when penalty payment is confirmed."""
        days_part = f"{days_count} روز — " if days_count > 1 else ""
        return (
            f"✅ جریمه {user_name} پرداخت شد.\n"
            f"{days_part}{amount:,} تومان"
        )

    @staticmethod
    def format_penalty_payment_receipt_caption(
        user_name: str, amount: int, days_count: int
    ) -> str:
        """Caption for receipt photo posted in group."""
        return (
            f"✅ جریمه {user_name} پرداخت شد\n\n"
            f"👤 {user_name}\n"
            f"📅 تعداد روز گزارش ثبت‌نشده: {days_count} روز\n"
            f"💰 مبلغ: {amount:,} تومان"
        )

    BROADCAST_HEADERS = {
        "admin": "📢 پیام ادمین",
        "bot": "🤖 پیام ربات",
    }

    @staticmethod
    def format_broadcast_message(text: str, message_type: str = "admin") -> str:
        """Format a dashboard broadcast with admin/bot header."""
        header = MessageFormatter.BROADCAST_HEADERS.get(
            message_type, MessageFormatter.BROADCAST_HEADERS["admin"]
        )
        body = (text or "").strip()
        return f"{header}\n{'─' * 20}\n{body}"

    @staticmethod
    def format_admin_weekly_summary(
        week_start: date,
        week_end: date,
        reports: List[Dict],
    ) -> str:
        """
        Format admin weekly summary with all users.
        
        Args:
            week_start: Start date of the week
            week_end: End date of the week
            reports: List of user reports
            
        Returns:
            str: Formatted admin summary
        """
        date_range = f"{gregorian_to_jalali_str(week_start)} تا {gregorian_to_jalali_str(week_end)}"
        v2 = period_uses_v2(week_start, week_end)
        labels = labels_for(week_end if v2 else week_start)
        
        message = f"📊 خلاصه هفتگی\n{date_range}\n{'=' * 40}\n"
        
        total_main = 0
        total_side = 0
        total_all = 0
        user_count = 0
        
        for report in reports:
            main = report.get("main_hours", 0)
            side = report.get("side_hours", 0)
            total = report.get("total_hours", main if v2 else main + side)
            
            if v2:
                pct = growth_percent(main, side)
                message += (
                    f"{report.get('user_name', 'نامشخص')}: "
                    f"{format_duration(main)} مفید · "
                    f"{format_duration(side)} رشد ({pct}%)\n"
                )
            else:
                message += (
                    f"{report.get('user_name', 'نامشخص')}: "
                    f"{format_duration(total)} ({format_duration(main)}+{format_duration(side)})\n"
                )
            
            total_main += main
            total_side += side
            total_all += total
            user_count += 1
        
        avg_total = (total_main if v2 else total_all) / user_count if user_count > 0 else 0
        
        message += f"\n{'=' * 40}\n"
        if v2:
            pct = growth_percent(total_main, total_side)
            message += (
                f"👥 کل کاربران: {user_count}\n"
                f"⬛️ کل {labels['first']}: {format_duration(total_main)}\n"
                f"🟢 کل {labels['second']}: {format_duration(total_side)}\n"
                f"📈 درصد رشد از ساعت کار: {pct} درصد\n"
                f"📊 میانگین مفید: {format_duration(avg_total)}"
            )
        else:
            message += (
                f"👥 کل کاربران: {user_count}\n"
                f"⬛️ کل اصلی: {format_duration(total_main)}\n"
                f"🔵 کل فرعی: {format_duration(total_side)}\n"
                f"📈 کل کل: {format_duration(total_all)}\n"
                f"📊 میانگین: {format_duration(avg_total)}"
            )
        
        return message
    
    @staticmethod
    def format_user_profile(
        user_name: str,
        phone: Optional[str] = None,
        bio: Optional[str] = None,
        interests: Optional[str] = None,
    ) -> str:
        """
        Format a user profile display.
        
        Args:
            user_name: User's full name
            phone: Phone number (optional)
            bio: User bio (optional)
            interests: User interests (optional)
            
        Returns:
            str: Formatted profile
        """
        message = f"👤 {user_name}\n"
        
        if phone:
            message += f"📞 {phone}\n"
        
        if bio:
            message += f"📝 {bio}\n"
        
        if interests:
            message += f"⭐ علاقه‌مندی‌ها: {interests}"
        
        return message
    
    @staticmethod
    def format_excel_header() -> List[str]:
        """
        Get headers for Excel export.
        
        Returns:
            List[str]: Column headers in Persian
        """
        return [
            "نام کاربر",
            "کل ساعت مفید",
            "جریمه‌ها",
            "تاریخ",
        ]
