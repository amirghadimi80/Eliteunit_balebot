"""
Report generation and statistics service.
Handles daily, weekly, and monthly reports with calculations.
"""

import logging
from typing import List, Tuple
from datetime import date, datetime, timedelta
from dataclasses import dataclass

from database.db import Database
from models.models import Report, DailyStats, WeeklyStats, MonthlyStats
from utils.date_utils import (
    get_today_gregorian,
    gregorian_to_jalali,
    gregorian_to_jalali_str,
    get_week_start_end,
    get_month_start_end,
)

logger = logging.getLogger(__name__)


class ReportService:
    """Service for generating and analyzing reports."""
    
    def __init__(self, db: Database):
        """
        Initialize report service.
        
        Args:
            db: Database instance
        """
        self.db = db
    
    # =====================
    # DAILY REPORT OPERATIONS
    # =====================

    def get_missing_report_dates(
        self, user_id: int, max_days_back: int = 31
    ) -> List[date]:
        """
        All calendar days before today without a report, oldest first.
        """
        today = get_today_gregorian()
        missing: List[date] = []
        d = today - timedelta(days=1)
        start = today - timedelta(days=max_days_back)

        while d >= start:
            if not self.db.report_exists(user_id, d.strftime("%Y-%m-%d")):
                missing.append(d)
            d -= timedelta(days=1)

        missing.sort()
        return missing

    def get_next_report_date(self, user_id: int) -> Tuple[date, bool]:
        """Next required report: oldest missing day, or today if caught up."""
        missing = self.get_missing_report_dates(user_id)
        if missing:
            return missing[0], True
        return get_today_gregorian(), False
    
    def submit_daily_report(
        self,
        user_id: int,
        main_hours: float,
        side_hours: float,
        report_date: date = None,
    ) -> Tuple[bool, str]:
        """
        Submit a daily report for a user.
        
        Args:
            user_id: User ID
            main_hours: Main working hours
            side_hours: Side working hours
            report_date: Date of report (defaults to today)
            
        Returns:
            Tuple[bool, str]: (success, message)
        """
        if report_date is None:
            report_date = get_today_gregorian()
        
        # Check if report already exists
        date_gregorian = report_date.strftime("%Y-%m-%d")
        if self.db.report_exists(user_id, date_gregorian):
            return False, "گزارش برای این تاریخ قبلاً ثبت شده است"
        
        # Validate hours
        if main_hours < 0 or side_hours < 0:
            return False, "ساعات نمی‌تواند منفی باشند"
        
        if main_hours > 12 or side_hours > 8:
            return False, "ساعات از حد مجاز بیشتر است"
        
        # Create report
        date_shamsi = gregorian_to_jalali_str(report_date)
        report = Report(
            user_id=user_id,
            date_shamsi=date_shamsi,
            date_gregorian=date_gregorian,
            main_hours=main_hours,
            side_hours=side_hours,
        )
        
        report_id = self.db.add_report(report)
        if report_id:
            logger.info(f"Report submitted: user_id={user_id}, date={date_shamsi}")
            return True, "گزارش با موفقیت ثبت شد ✅"
        
        return False, "خطا در ثبت گزارش"
    
    def get_today_all_reports(self) -> List[Tuple[Report, str]]:
        """
        Get all reports for today with user names.
        
        Returns:
            List[Tuple[Report, str]]: List of (report, user_name) tuples
        """
        today = get_today_gregorian()
        date_gregorian = today.strftime("%Y-%m-%d")
        
        reports = self.db.get_reports_by_date(date_gregorian)
        
        results = []
        for report in reports:
            user = self.db.get_user_by_id(report.user_id)
            if user:
                results.append((report, user.full_name))
        
        return results
    
    def get_daily_stats(self, report_date: date = None) -> DailyStats:
        """
        Get daily statistics for a specific date.
        
        Args:
            report_date: Date to get stats for (defaults to today)
            
        Returns:
            DailyStats: Daily statistics
        """
        if report_date is None:
            report_date = get_today_gregorian()
        
        date_gregorian = report_date.strftime("%Y-%m-%d")
        reports = self.db.get_reports_by_date(date_gregorian)
        
        # Get all users for missing reports count
        all_users = self.db.get_all_users()
        
        total_main = sum(r.main_hours for r in reports)
        total_side = sum(r.side_hours for r in reports)
        total = total_main + total_side
        
        missing = len(all_users) - len(reports)
        
        avg_per_user = total / len(reports) if reports else 0
        
        stats = DailyStats(
            report_date=report_date,
            total_users_reported=len(reports),
            total_main_hours=total_main,
            total_side_hours=total_side,
            total_hours=total,
            avg_hours_per_user=avg_per_user,
            missing_reports=missing,
        )
        
        logger.info(f"Daily stats calculated: {stats}")
        return stats
    
    # =====================
    # WEEKLY REPORT OPERATIONS
    # =====================
    
    def get_weekly_stats(self, user_id: int) -> WeeklyStats:
        """
        Get weekly statistics for a user.
        
        Args:
            user_id: User ID
            
        Returns:
            WeeklyStats: Weekly statistics
        """
        week_start, week_end = get_week_start_end()
        start_gregorian = week_start.strftime("%Y-%m-%d")
        end_gregorian = week_end.strftime("%Y-%m-%d")
        
        reports = self.db.get_reports_by_user_and_date(
            user_id,
            start_gregorian,
            end_gregorian
        )
        
        total_main = sum(r.main_hours for r in reports)
        total_side = sum(r.side_hours for r in reports)
        total = total_main + total_side
        
        stats = WeeklyStats(
            user_id=user_id,
            week_start=week_start,
            week_end=week_end,
            main_hours=total_main,
            side_hours=total_side,
            total_hours=total,
            days_reported=len(reports),
        )
        
        logger.info(f"Weekly stats calculated: {stats}")
        return stats
    
    def get_all_weekly_stats(self) -> List[Tuple[WeeklyStats, str]]:
        """
        Get weekly statistics for all users.
        
        Returns:
            List[Tuple[WeeklyStats, str]]: List of (stats, user_name) tuples
        """
        users = self.db.get_all_users()
        results = []
        
        for user in users:
            stats = self.get_weekly_stats(user.id)
            results.append((stats, user.full_name))
        
        return results
    
    # =====================
    # MONTHLY REPORT OPERATIONS
    # =====================
    
    def get_monthly_stats(self, user_id: int, year: int = None, month: int = None) -> MonthlyStats:
        """
        Get monthly statistics for a user.
        
        Args:
            user_id: User ID
            year: Jalali year (defaults to current)
            month: Jalali month (defaults to current)
            
        Returns:
            MonthlyStats: Monthly statistics
        """
        if year is None or month is None:
            month_start, month_end = get_month_start_end()
            # Convert to Jalali to get year and month
            jy, jm, _ = gregorian_to_jalali(month_start)
            year = year or jy
            month = month or jm
        
        # This requires converting Jalali dates to Gregorian for DB query
        # For now, use current month
        month_start, month_end = get_month_start_end()
        start_gregorian = month_start.strftime("%Y-%m-%d")
        end_gregorian = month_end.strftime("%Y-%m-%d")
        
        reports = self.db.get_reports_by_user_and_date(
            user_id,
            start_gregorian,
            end_gregorian
        )
        
        total_main = sum(r.main_hours for r in reports)
        total_side = sum(r.side_hours for r in reports)
        total = total_main + total_side
        
        # Calculate days in month
        days_in_month = (month_end - month_start).days + 1
        
        stats = MonthlyStats(
            user_id=user_id,
            year=year,
            month=month,
            main_hours=total_main,
            side_hours=total_side,
            total_hours=total,
            days_reported=len(reports),
            days_total=days_in_month,
        )
        
        logger.info(f"Monthly stats calculated: {stats}")
        return stats
    
    def get_all_monthly_stats(self, year: int = None, month: int = None) -> List[Tuple[MonthlyStats, str]]:
        """
        Get monthly statistics for all users.
        
        Args:
            year: Jalali year (defaults to current)
            month: Jalali month (defaults to current)
            
        Returns:
            List[Tuple[MonthlyStats, str]]: List of (stats, user_name) tuples
        """
        users = self.db.get_all_users()
        results = []
        
        for user in users:
            stats = self.get_monthly_stats(user.id, year, month)
            results.append((stats, user.full_name))
        
        return results
    
    # =====================
    # EXPORT OPERATIONS
    # =====================
    
    def get_excel_export_data(self, stats_list: List[Tuple]) -> List[dict]:
        """
        Prepare data for Excel export.
        
        Args:
            stats_list: List of (stats, user_name) tuples
            
        Returns:
            List[dict]: List of dictionaries for Excel rows
        """
        from utils.date_utils import get_today_gregorian
        
        today = get_today_gregorian()
        export_data = []
        
        for stats, user_name in stats_list:
            # Determine stats type based on attributes
            if hasattr(stats, 'week_start'):
                date_str = f"{gregorian_to_jalali_str(stats.week_start)} - {gregorian_to_jalali_str(stats.week_end)}"
            elif hasattr(stats, 'month'):
                date_str = f"{stats.year:04d}/{stats.month:02d}"
            else:
                date_str = gregorian_to_jalali_str(today)
            
            # Get penalty count for this user
            from database.db import Database
            db = Database()
            penalties = db.get_penalties_by_user(stats.user_id, status="unpaid")
            penalty_count = sum(p.amount for p in penalties)
            
            export_data.append({
                "نام کاربر": user_name,
                "ساعت اصلی": stats.main_hours,
                "ساعت فرعی": stats.side_hours,
                "کل ساعات": stats.total_hours,
                "جریمه‌ها": penalty_count,
                "تاریخ": date_str,
            })
        
        return export_data
