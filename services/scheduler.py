"""
Scheduler service for recurring tasks using APScheduler.
Handles penalty checks, reminders, and automated reporting.
"""

import logging
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from database.db import Database
from services.penalty import PenaltyService
from services.notifications import notify_penalty_created
from config.settings import MISSING_REPORT_CHECK_HOUR, MISSING_REPORT_CHECK_MINUTE, TIMEZONE

logger = logging.getLogger(__name__)


class SchedulerService:
    """Service for managing scheduled tasks."""

    def __init__(self, db: Database):
        self.db = db
        self.penalty_service = PenaltyService(db)
        self.scheduler = BackgroundScheduler(timezone=TIMEZONE)
        self.bot_instance = None

    def set_bot_instance(self, bot):
        self.bot_instance = bot

    def start(self):
        if self.scheduler.running:
            logger.warning("Scheduler is already running")
            return
        self._add_missing_report_check_job()
        self.scheduler.start()
        logger.info("Scheduler started successfully")

    def stop(self):
        if not self.scheduler.running:
            logger.warning("Scheduler is not running")
            return
        self.scheduler.shutdown()
        logger.info("Scheduler stopped")

    def _add_missing_report_check_job(self):
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
        """Create penalties and notify users + groups."""
        try:
            logger.info("Starting missing report check job")
            created = self.penalty_service.check_and_create_missing_report_penalties()

            for item in created:
                try:
                    notify_penalty_created(
                        user_name=item.user_name,
                        bale_id=item.bale_id,
                        date_shamsi=item.date_shamsi,
                        amount=item.amount,
                        consecutive_days=item.consecutive_days,
                    )
                except Exception as e:
                    logger.error(f"Error notifying {item.user_name}: {e}")

            logger.info(f"Missing report check completed. Penalties created: {len(created)}")
        except Exception as e:
            logger.error(f"Error in missing report check job: {e}")

    def trigger_manual_check(self) -> int:
        created = self.penalty_service.check_and_create_missing_report_penalties()
        for item in created:
            notify_penalty_created(
                user_name=item.user_name,
                bale_id=item.bale_id,
                date_shamsi=item.date_shamsi,
                amount=item.amount,
                consecutive_days=item.consecutive_days,
            )
        return len(created)

    def get_jobs(self):
        return self.scheduler.get_jobs()

    def is_running(self) -> bool:
        return self.scheduler.running
