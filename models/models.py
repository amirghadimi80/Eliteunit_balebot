"""
Data models and classes for EliteUniteTime system.
Contains User, Report, and Penalty data classes.
"""

from dataclasses import dataclass
from typing import Optional
from datetime import datetime, date


@dataclass
class User:
    """User data model."""
    
    bale_id: int
    full_name: str
    phone: Optional[str] = None
    bio: Optional[str] = None
    interests: Optional[str] = None
    id: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def __repr__(self) -> str:
        """String representation of User."""
        return f"User(id={self.id}, bale_id={self.bale_id}, name={self.full_name})"


@dataclass
class Report:
    """Daily report data model."""
    
    user_id: int
    date_shamsi: str  # Format: YYYY/MM/DD
    date_gregorian: str  # Format: YYYY-MM-DD
    main_hours: float = 0.0
    side_hours: float = 0.0
    total_hours: float = 0.0
    id: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def __post_init__(self):
        """Calculate total hours after initialization."""
        self.total_hours = self.main_hours + self.side_hours
    
    def __repr__(self) -> str:
        """String representation of Report."""
        return (
            f"Report(id={self.id}, user_id={self.user_id}, "
            f"date={self.date_shamsi}, total={self.total_hours}h)"
        )


@dataclass
class Penalty:
    """Penalty record data model."""
    
    user_id: int
    date_shamsi: str  # Format: YYYY/MM/DD
    date_gregorian: str  # Format: YYYY-MM-DD
    reason: str
    amount: int = 1
    status: str = "unpaid"  # unpaid or paid
    id: Optional[int] = None
    created_at: Optional[datetime] = None
    
    def __repr__(self) -> str:
        """String representation of Penalty."""
        return (
            f"Penalty(id={self.id}, user_id={self.user_id}, "
            f"date={self.date_shamsi}, status={self.status})"
        )


@dataclass
class UserProfile:
    """Extended user profile for social discovery."""
    
    user: User
    total_reports: int = 0
    total_hours: float = 0.0
    avg_daily_hours: float = 0.0
    penalties_unpaid: int = 0
    
    def __repr__(self) -> str:
        """String representation of UserProfile."""
        return (
            f"UserProfile(user={self.user.full_name}, "
            f"total_reports={self.total_reports}, "
            f"total_hours={self.total_hours:.1f}h)"
        )


@dataclass
class DailyStats:
    """Daily group statistics."""
    
    report_date: date
    total_users_reported: int = 0
    total_main_hours: float = 0.0
    total_side_hours: float = 0.0
    total_hours: float = 0.0
    avg_hours_per_user: float = 0.0
    missing_reports: int = 0
    
    def __repr__(self) -> str:
        """String representation of DailyStats."""
        return (
            f"DailyStats(date={self.report_date}, "
            f"users_reported={self.total_users_reported}, "
            f"total_hours={self.total_hours:.1f}h)"
        )


@dataclass
class WeeklyStats:
    """Weekly statistics for a user."""
    
    user_id: int
    week_start: date
    week_end: date
    main_hours: float = 0.0
    side_hours: float = 0.0
    total_hours: float = 0.0
    days_reported: int = 0
    
    def __repr__(self) -> str:
        """String representation of WeeklyStats."""
        return (
            f"WeeklyStats(user_id={self.user_id}, "
            f"total_hours={self.total_hours:.1f}h, "
            f"days={self.days_reported})"
        )


@dataclass
class MonthlyStats:
    """Monthly statistics for a user."""
    
    user_id: int
    year: int
    month: int
    main_hours: float = 0.0
    side_hours: float = 0.0
    total_hours: float = 0.0
    days_reported: int = 0
    days_total: int = 31
    
    def __repr__(self) -> str:
        """String representation of MonthlyStats."""
        return (
            f"MonthlyStats(user_id={self.user_id}, "
            f"month={self.year:04d}/{self.month:02d}, "
            f"total_hours={self.total_hours:.1f}h)"
        )
