"""
Penalty management service for handling missing reports and penalties.
"""

import logging
from typing import List, Tuple
from datetime import date, datetime, timedelta

from database.db import Database
from models.models import Penalty
from utils.date_utils import (
    get_today_gregorian,
    get_yesterday,
    gregorian_to_jalali_str,
)
from config.settings import PENALTY_AMOUNT

logger = logging.getLogger(__name__)


class PenaltyService:
    """Service for managing penalties and missing reports."""
    
    def __init__(self, db: Database):
        """
        Initialize penalty service.
        
        Args:
            db: Database instance
        """
        self.db = db
    
    def check_and_create_missing_report_penalties(self) -> List[Tuple[int, str, str]]:
        """
        Check yesterday's reports and create penalties for missing ones.
        Called daily at 10 AM Iran time.
        
        Returns:
            List[Tuple[int, str, str]]: List of (user_id, full_name, date_shamsi) 
                                        for which penalties were created
        """
        yesterday = get_yesterday()
        yesterday_gregorian = yesterday.strftime("%Y-%m-%d")
        
        # Get all users who didn't report yesterday
        missing_users = self.db.get_missing_report_users(yesterday_gregorian)
        
        created_penalties = []
        
        for user_id, user_name in missing_users:
            # Check if penalty already exists for this date
            existing_penalties = self.db.get_penalties_by_user(user_id)
            penalty_exists = any(p.date_gregorian == yesterday_gregorian for p in existing_penalties)
            
            if not penalty_exists:
                # Create penalty record
                penalty = Penalty(
                    user_id=user_id,
                    date_shamsi=gregorian_to_jalali_str(yesterday),
                    date_gregorian=yesterday_gregorian,
                    reason=f"عدم ثبت گزارش روز {gregorian_to_jalali_str(yesterday)}",
                    amount=PENALTY_AMOUNT,
                    status="unpaid",
                )
                
                penalty_id = self.db.add_penalty(penalty)
                if penalty_id:
                    created_penalties.append((user_id, user_name, penalty.date_shamsi))
                    logger.info(f"Penalty created for user {user_name}: {penalty.reason}")
        
        return created_penalties
    
    def get_user_unpaid_penalties(self, user_id: int) -> List[Penalty]:
        """
        Get all unpaid penalties for a user.
        
        Args:
            user_id: User ID
            
        Returns:
            List[Penalty]: List of unpaid penalties
        """
        return self.db.get_penalties_by_user(user_id, status="unpaid")
    
    def get_user_all_penalties(self, user_id: int) -> List[Penalty]:
        """
        Get all penalties for a user.
        
        Args:
            user_id: User ID
            
        Returns:
            List[Penalty]: List of all penalties
        """
        return self.db.get_penalties_by_user(user_id)
    
    def mark_penalty_as_paid(self, penalty_id: int) -> bool:
        """
        Mark a penalty as paid.
        
        Args:
            penalty_id: Penalty ID
            
        Returns:
            bool: True if successful
        """
        return self.db.mark_penalty_paid(penalty_id)
    
    def get_total_unpaid_penalty_count(self, user_id: int) -> int:
        """
        Get total count of unpaid penalties for a user.
        
        Args:
            user_id: User ID
            
        Returns:
            int: Count of unpaid penalties
        """
        unpaid = self.get_user_unpaid_penalties(user_id)
        return sum(p.amount for p in unpaid)
    
    def get_user_missing_dates(self, user_id: int, days_back: int = 7) -> List[str]:
        """
        Get list of dates for which user has penalties in the last N days.
        
        Args:
            user_id: User ID
            days_back: Number of days to look back
            
        Returns:
            List[str]: List of dates in Jalali format (YYYY/MM/DD)
        """
        penalties = self.get_user_all_penalties(user_id)
        
        cutoff_date = get_today_gregorian() - timedelta(days=days_back)
        
        missing_dates = [
            p.date_shamsi for p in penalties
            if datetime.strptime(p.date_gregorian, "%Y-%m-%d").date() >= cutoff_date
        ]
        
        return sorted(missing_dates, reverse=True)
    
    def get_all_unpaid_penalties_summary(self) -> dict:
        """
        Get a summary of all unpaid penalties in the system.
        
        Returns:
            dict: Summary with user names and penalty counts
        """
        users = self.db.get_all_users()
        summary = {}
        
        for user in users:
            unpaid_count = self.get_total_unpaid_penalty_count(user.id)
            if unpaid_count > 0:
                summary[user.full_name] = unpaid_count
        
        return summary
