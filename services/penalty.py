"""
Penalty management service for handling missing reports and penalties.
"""

import logging
from dataclasses import dataclass
from typing import List
from datetime import date, datetime, timedelta

from database.db import Database
from models.models import Penalty
from utils.date_utils import (
    get_today_gregorian,
    get_yesterday,
    gregorian_to_jalali_str,
)
from config.settings import PENALTY_AMOUNT_ONE_DAY, PENALTY_AMOUNT_TWO_DAYS

logger = logging.getLogger(__name__)


@dataclass
class CreatedPenalty:
    """Info about a newly created penalty (for notifications)."""

    penalty_id: int
    user_id: int
    user_name: str
    bale_id: int
    date_shamsi: str
    date_gregorian: str
    amount: int
    consecutive_days: int


class PenaltyService:
    """Service for managing penalties and missing reports."""

    def __init__(self, db: Database):
        self.db = db

    def _consecutive_missed_days(self, user_id: int, end_date: date) -> int:
        """Count consecutive days without report ending on end_date (inclusive)."""
        count = 0
        d = end_date
        while not self.db.report_exists(user_id, d.strftime("%Y-%m-%d")):
            count += 1
            d -= timedelta(days=1)
            if count > 31:
                break
        return count

    def _calculate_amount(self, consecutive_days: int) -> int:
        if consecutive_days >= 2:
            return PENALTY_AMOUNT_TWO_DAYS
        return PENALTY_AMOUNT_ONE_DAY

    def check_and_create_missing_report_penalties(self) -> List[CreatedPenalty]:
        """
        Check yesterday's reports and create penalties for missing ones.
        Runs daily at 10 AM Iran time — users had until then to submit yesterday's report.

        Returns:
            List of newly created penalties (for notifications).
        """
        yesterday = get_yesterday()
        yesterday_gregorian = yesterday.strftime("%Y-%m-%d")
        missing_users = self.db.get_missing_report_users(yesterday_gregorian)

        created: List[CreatedPenalty] = []

        for user_id, user_name in missing_users:
            existing = self.db.get_penalties_by_user(user_id)
            if any(p.date_gregorian == yesterday_gregorian for p in existing):
                continue

            consecutive = self._consecutive_missed_days(user_id, yesterday)
            amount = self._calculate_amount(consecutive)
            date_shamsi = gregorian_to_jalali_str(yesterday)

            if consecutive >= 2:
                reason = (
                    f"عدم ثبت گزارش {consecutive} روز متوالی "
                    f"(آخرین روز: {date_shamsi})"
                )
            else:
                reason = f"عدم ثبت گزارش روز {date_shamsi}"

            penalty = Penalty(
                user_id=user_id,
                date_shamsi=date_shamsi,
                date_gregorian=yesterday_gregorian,
                reason=reason,
                amount=amount,
                status="unpaid",
            )

            penalty_id = self.db.add_penalty(penalty)
            if penalty_id:
                user = self.db.get_user_by_id(user_id)
                bale_id = user.bale_id if user else 0
                created.append(
                    CreatedPenalty(
                        penalty_id=penalty_id,
                        user_id=user_id,
                        user_name=user_name,
                        bale_id=bale_id,
                        date_shamsi=date_shamsi,
                        date_gregorian=yesterday_gregorian,
                        amount=amount,
                        consecutive_days=consecutive,
                    )
                )
                logger.info(
                    f"Penalty created: {user_name} — {amount} Toman "
                    f"({consecutive} day(s) missed)"
                )

        return created

    def get_user_unpaid_penalties(self, user_id: int) -> List[Penalty]:
        return self.db.get_penalties_by_user(user_id, status="unpaid")

    def get_user_all_penalties(self, user_id: int) -> List[Penalty]:
        return self.db.get_penalties_by_user(user_id)

    def mark_penalty_as_paid(self, penalty_id: int) -> bool:
        return self.db.mark_penalty_paid(penalty_id)

    def get_total_unpaid_penalty_amount(self, user_id: int) -> int:
        unpaid = self.get_user_unpaid_penalties(user_id)
        return sum(p.amount for p in unpaid)

    def get_user_missing_dates(self, user_id: int, days_back: int = 7) -> List[str]:
        penalties = self.get_user_all_penalties(user_id)
        cutoff_date = get_today_gregorian() - timedelta(days=days_back)
        missing_dates = [
            p.date_shamsi
            for p in penalties
            if datetime.strptime(p.date_gregorian, "%Y-%m-%d").date() >= cutoff_date
        ]
        return sorted(missing_dates, reverse=True)

    def get_all_unpaid_penalties_summary(self) -> dict:
        users = self.db.get_all_users()
        summary = {}
        for user in users:
            total = self.get_total_unpaid_penalty_amount(user.id)
            if total > 0:
                summary[user.full_name] = total
        return summary

    def get_recent_unpaid_penalties(self, limit: int = 10) -> List[dict]:
        """Recent unpaid penalties with user info for dashboard."""
        rows = []
        for p in self.db.get_all_penalties():
            if p.status != "unpaid":
                continue
            user = self.db.get_user_by_id(p.user_id)
            if user:
                rows.append({
                    "id": p.id,
                    "user_name": user.full_name,
                    "date_shamsi": p.date_shamsi,
                    "amount": p.amount,
                    "reason": p.reason,
                })
            if len(rows) >= limit:
                break
        return rows
