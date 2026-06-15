"""
Bale message notifications for penalties (user DM + group).
Uses Bale HTTP API directly so it works from scheduler and Flask.
"""

import logging
from typing import Optional

import httpx

from config.settings import BALE_API_TOKEN, BALE_GROUP_IDS
from utils.formatter import MessageFormatter

logger = logging.getLogger(__name__)


def send_bale_message(chat_id: int, text: str) -> bool:
    """Send a text message via Bale bot API."""
    if not BALE_API_TOKEN:
        logger.error("BALE_API_TOKEN not set — cannot send message")
        return False
    try:
        response = httpx.post(
            f"https://tapi.bale.ai/bot{BALE_API_TOKEN}/sendMessage",
            json={"chat_id": chat_id, "text": text},
            timeout=15,
        )
        if response.status_code != 200:
            logger.error(f"Bale API error {response.status_code}: {response.text[:200]}")
            return False
        return True
    except Exception as e:
        logger.error(f"Failed to send Bale message to {chat_id}: {e}")
        return False


def send_to_groups(text: str) -> int:
    """Send message to all configured groups. Returns count of successful sends."""
    sent = 0
    for group_id in BALE_GROUP_IDS:
        if send_bale_message(group_id, text):
            sent += 1
    return sent


def notify_penalty_created(
    user_name: str,
    bale_id: int,
    date_shamsi: str,
    amount: int,
    consecutive_days: int,
) -> None:
    """Notify user (DM) and groups about a new penalty."""
    user_msg = MessageFormatter.format_penalty_user_message(
        user_name, amount, date_shamsi, consecutive_days
    )
    group_msg = MessageFormatter.format_penalty_group_message(
        user_name, amount, date_shamsi, consecutive_days
    )

    if bale_id:
        send_bale_message(bale_id, user_msg)
    send_to_groups(group_msg)
    logger.info(f"Penalty notifications sent for {user_name} ({amount} Toman)")


def notify_penalty_paid(user_name: str, bale_id: Optional[int], amount: int) -> None:
    """Notify user and groups that a penalty was paid."""
    msg = MessageFormatter.format_penalty_paid_message(user_name, amount)
    if bale_id:
        send_bale_message(bale_id, msg)
    send_to_groups(msg)
    logger.info(f"Penalty paid notifications sent for {user_name}")
