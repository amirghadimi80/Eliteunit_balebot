"""
Scheduler service for recurring tasks using APScheduler.
Handles penalty checks, reminders, and automated reporting.
"""

import logging
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
import pytz

from database.db import Database
from services.penalty import PenaltyService
from config.settings import MISSING_REPORT_CHECK_HOUR, MISSING_REPORT_CHECK_MINUTE, TIMEZONE

logger = logging.getLogger(__name__)


class SchedulerService:
    """Service for managing scheduled tasks."""
    
    def __init__(self, db: Database):
        """
        Initialize scheduler service.
        
        Args:
            db: Database instance
        """
        self.db = db
        self.penalty_service = PenaltyService(db)
        self.scheduler = BackgroundScheduler(timezone=TIMEZONE)
        self.bot_instance = None  # Will be set from bot.py
    
    def set_bot_instance(self, bot):
        """
        Set the bot instance for sending messages.
        
        Args:
            bot: Balethon bot instance
        """
        self.bot_instance = bot
    
    def start(self):
        """Start the scheduler."""
        if self.scheduler.running:
            logger.warning("Scheduler is already running")
            return
        
        # Add jobs
        self._add_missing_report_check_job()
        
        self.scheduler.start()
        logger.info("Scheduler started successfully")
    
    def stop(self):
        """Stop the scheduler."""
        if not self.scheduler.running:
            logger.warning("Scheduler is not running")
            return
        
        self.scheduler.shutdown()
        logger.info("Scheduler stopped")
    
    def _add_missing_report_check_job(self):
        """
        Add a job to check for missing reports daily at 10 AM Iran time.
        This job creates penalties for users who didn't report the previous day.
        """
        # Create a cron trigger for daily check at specified time
        trigger = CronTrigger(
            hour=MISSING_REPORT_CHECK_HOUR,
            minute=MISSING_REPORT_CHECK_MINUTE,
            timezone=TIMEZONE,
        )
        
        self.scheduler.add_job(
            func=self._check_missing_reports,
            trigger=trigger,
            id="check_missing_reports",
            name="Check missing daily reports",
            replace_existing=True,
        )
        
        logger.info(
            f"Missing report check job added: daily at "
            f"{MISSING_REPORT_CHECK_HOUR:02d}:{MISSING_REPORT_CHECK_MINUTE:02d} {TIMEZONE}"
        )
    
    def _check_missing_reports(self):
        """
        Check yesterday's reports and create penalties for missing ones.
        Called by the scheduler daily.
        """
        try:
            logger.info("Starting missing report check job")
            
            # Create penalties for missing reports
            created_penalties = self.penalty_service.check_and_create_missing_report_penalties()
            
            if created_penalties and self.bot_instance:
                # Notify users about their penalties
                for user_id, user_name, date_shamsi in created_penalties:
                    try:
                        user = self.db.get_user_by_id(user_id)
                        if user:
                            message = (
                                f"⚠️ تنبیه برای شما\n\n"
                                f"گزارش روز {date_shamsi} را ثبت نکردید.\n"
                                f"لطفاً در اسرع وقت گزارش خود را ثبت کنید."
                            )
                            # This would be called if bot has a method to send private messages
                            # For now, just log it
                            logger.info(f"Penalty notification would be sent to user {user_name}")
                    except Exception as e:
                        logger.error(f"Error notifying user {user_name}: {e}")
            
            logger.info(f"Missing report check completed. Penalties created: {len(created_penalties)}")
        
        except Exception as e:
            logger.error(f"Error in missing report check job: {e}")
    
    def trigger_manual_check(self):
        """
        Manually trigger the missing report check.
        Useful for testing or manual triggers.
        
        Returns:
            int: Number of penalties created
        """
        created_penalties = self.penalty_service.check_and_create_missing_report_penalties()
        return len(created_penalties)
    
    def get_jobs(self):
        """
        Get all scheduled jobs.
        
        Returns:
            list: List of scheduled jobs
        """
        return self.scheduler.get_jobs()
    
    def is_running(self) -> bool:
        """
        Check if scheduler is running.
        
        Returns:
            bool: True if scheduler is running
        """
        return self.scheduler.running
