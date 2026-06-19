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
    ) -> str:
        """
        Format a daily report message for group notification.

        Args:
            user_name: User's full name
            main_hours: Main working hours
            side_hours: Secondary hours
            total_hours: Total hours
            report_date: Date of the report
            submit_time: Time of submission (HH:MM, Iran time)

        Returns:
            str: Formatted report message
        """
        date_str = format_date_persian(report_date)
        time_part = f"  🕐 {submit_time}" if submit_time else ""

        message = (
            f"👤 {user_name}\n"
            f"📌 اصلی: {main_hours}\n"
            f"📌 فرعی: {side_hours}\n"
            f"➕ مجموع: {total_hours}\n"
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
        
        message = f"📊 خلاصه روزانه - {date_str}\n{'=' * 40}\n"
        
        total_main = 0
        total_side = 0
        total_all = 0
        
        for report in reports:
            main = report.get("main_hours", 0)
            side = report.get("side_hours", 0)
            total = report.get("total_hours", 0)
            
            message += (
                f"👤 {report.get('user_name', 'نامشخص')}: "
                f"{total} ساعت (⬛️{main} + 🔵{side})\n"
            )
            
            total_main += main
            total_side += side
            total_all += total
        
        message += f"\n{'=' * 40}\n"
        message += (
            f"📈 کل: {total_all} ساعت\n"
            f"⬛️ اصلی: {total_main} | 🔵 فرعی: {total_side}"
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
        """
        Format a weekly report for a user.
        
        Args:
            user_name: User's full name
            week_start: Start date of the week
            week_end: End date of the week
            main_hours: Total main hours
            side_hours: Total side hours
            total_hours: Total hours
            
        Returns:
            str: Formatted weekly report
        """
        date_range = f"{gregorian_to_jalali_str(week_start)} تا {gregorian_to_jalali_str(week_end)}"
        
        message = (
            f"📈 گزارش هفتگی\n"
            f"👤 {user_name}\n"
            f"📅 {date_range}\n\n"
            f"⬛️ ساعت اصلی: {main_hours}\n"
            f"🔵 ساعت فرعی: {side_hours}\n"
            f"➕ مجموع: {total_hours}"
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
    ) -> str:
        """
        Format a monthly report for a user.
        
        Args:
            user_name: User's full name
            year: Jalali year
            month: Jalali month
            main_hours: Total main hours
            side_hours: Total side hours
            total_hours: Total hours
            days_reported: Number of days with reports
            days_total: Total days in month
            
        Returns:
            str: Formatted monthly report
        """
        message = (
            f"📅 گزارش ماهانه\n"
            f"👤 {user_name}\n"
            f"🗓️  {year:04d}/{month:02d}\n\n"
            f"⬛️ ساعت اصلی: {main_hours}\n"
            f"🔵 ساعت فرعی: {side_hours}\n"
            f"➕ مجموع: {total_hours}\n\n"
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
    def _bot_report_reminder() -> str:
        return (
            "📝 گزارش را داخل بات ثبت کنید:\n"
            "منو → 📊 ثبت گزارش روزانه\n\n"
            "⚠️ اول گزارش دیروز را وارد کنید، سپس گزارش امروز."
        )

    @staticmethod
    def format_penalty_user_message(
        user_name: str,
        amount: int,
        date_shamsi: str,
        consecutive_days: int,
    ) -> str:
        """Private message to penalized user."""
        days_note = ""
        if consecutive_days >= 2:
            days_note = f"\n({consecutive_days} روز متوالی گزارش ثبت نشده)"
        return (
            f"⚠️ {user_name} عزیز\n\n"
            f"شما {amount:,} تومان جریمه شدید.{days_note}\n"
            f"گزارش روز {date_shamsi} ثبت نشده.\n"
            f"مهلت: تا ساعت ۱۰ صبح روز بعد.\n\n"
            f"{MessageFormatter._bot_report_reminder()}\n\n"
            f"{MessageFormatter._payment_block()}"
        )

    @staticmethod
    def format_penalty_group_message(
        user_name: str,
        amount: int,
        date_shamsi: str,
        consecutive_days: int,
    ) -> str:
        """Group announcement for a new penalty."""
        days_note = ""
        if consecutive_days >= 2:
            days_note = f" ({consecutive_days} روز متوالی)"
        return (
            f"⚠️ {user_name} — {amount:,} تومان جریمه شد{days_note}\n"
            f"گزارش روز {date_shamsi} ثبت نشده.\n\n"
            f"{MessageFormatter._bot_report_reminder()}\n\n"
            f"{MessageFormatter._payment_block()}"
        )

    @staticmethod
    def format_penalty_paid_message(user_name: str, amount: int) -> str:
        """Notification when penalty payment is confirmed."""
        return (
            f"✅ جریمه {user_name} ({amount:,} تومان) پرداخت شد.\n"
            f"تأیید شده توسط {PAYMENT_CARD_HOLDER}"
        )
    
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
        
        message = f"📊 خلاصه هفتگی\n{date_range}\n{'=' * 40}\n"
        
        total_main = 0
        total_side = 0
        total_all = 0
        user_count = 0
        
        for report in reports:
            main = report.get("main_hours", 0)
            side = report.get("side_hours", 0)
            total = report.get("total_hours", 0)
            
            message += (
                f"{report.get('user_name', 'نامشخص')}: "
                f"{total}h ({main}+{side})\n"
            )
            
            total_main += main
            total_side += side
            total_all += total
            user_count += 1
        
        avg_total = total_all / user_count if user_count > 0 else 0
        
        message += f"\n{'=' * 40}\n"
        message += (
            f"👥 کل کاربران: {user_count}\n"
            f"⬛️ کل اصلی: {total_main}\n"
            f"🔵 کل فرعی: {total_side}\n"
            f"📈 کل کل: {total_all}\n"
            f"📊 میانگین: {avg_total:.1f}"
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
            "ساعت اصلی",
            "ساعت فرعی",
            "کل ساعات",
            "جریمه‌ها",
            "تاریخ",
        ]
