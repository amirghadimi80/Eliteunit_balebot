"""
Bale message notifications for penalties (user DM + group).
Uses Bale HTTP API directly so it works from scheduler and Flask.
"""

import logging
from typing import Optional, TYPE_CHECKING

import httpx

from config.settings import BALE_API_TOKEN, BALE_GROUP_IDS
from utils.formatter import MessageFormatter

if TYPE_CHECKING:
    from balethon import Client
    from balethon.objects import Message

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
) -> None:
    """Notify user (DM) and groups about a new penalty."""
    user_msg = MessageFormatter.format_penalty_user_message(
        user_name, amount, date_shamsi
    )
    group_msg = MessageFormatter.format_penalty_group_message(
        user_name, amount, date_shamsi
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


async def _download_bale_file(client: "Client", file_id: str) -> bytes:
    """Download file bytes from Bale (file_id from user chat may not work in groups)."""
    file = await client.get_file(file_id)
    if file.path:
        url = f"{client.connection.base_url}/file/bot{client.connection.token}/{file.path}"
    else:
        url = client.connection.file_url(file_id)
    response = await client.connection.client.get(url, timeout=30)
    response.raise_for_status()
    return response.content


async def send_receipt_to_groups(
    client: "Client",
    message: "Message",
    file_id: str,
    caption: str,
) -> int:
    """
    Send receipt image + caption to all groups.
    Re-uploads the image so it works across chats; falls back to forward + text.
    Returns count of successful group sends.
    """
    sent = 0
    for group_id in BALE_GROUP_IDS:
        try:
            photo_bytes = await _download_bale_file(client, file_id)
            await client.send_photo(
                chat_id=group_id,
                photo=photo_bytes,
                caption=caption,
            )
            sent += 1
            logger.info(f"Receipt photo+caption sent to group {group_id}")
        except Exception as e:
            logger.warning(
                f"Re-upload receipt to {group_id} failed ({e}), trying forward"
            )
            try:
                await message.forward(group_id)
                await client.send_message(chat_id=group_id, text=caption)
                sent += 1
                logger.info(f"Receipt forwarded + caption sent to group {group_id}")
            except Exception as e2:
                logger.error(f"Failed to send receipt to group {group_id}: {e2}")
    return sent
