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


def send_bale_message(chat_id: int, text: str) -> Optional[int]:
    """
    Send a text message via Bale bot API.
    Returns message_id on success, None on failure.
    """
    if not BALE_API_TOKEN:
        logger.error("BALE_API_TOKEN not set — cannot send message")
        return None
    try:
        response = httpx.post(
            f"https://tapi.bale.ai/bot{BALE_API_TOKEN}/sendMessage",
            json={"chat_id": chat_id, "text": text},
            timeout=15,
        )
        if response.status_code != 200:
            logger.error(f"Bale API error {response.status_code}: {response.text[:200]}")
            return None
        data = response.json()
        result = data.get("result") or {}
        message_id = result.get("message_id")
        if message_id is None:
            logger.warning(f"Bale sendMessage ok but no message_id for chat {chat_id}")
            return None
        return int(message_id)
    except Exception as e:
        logger.error(f"Failed to send Bale message to {chat_id}: {e}")
        return None


def delete_bale_message(chat_id: int, message_id: int) -> bool:
    """Delete a message via Bale bot API (deleteMessage)."""
    if not BALE_API_TOKEN:
        logger.error("BALE_API_TOKEN not set — cannot delete message")
        return False
    try:
        response = httpx.post(
            f"https://tapi.bale.ai/bot{BALE_API_TOKEN}/deleteMessage",
            json={"chat_id": chat_id, "message_id": message_id},
            timeout=15,
        )
        if response.status_code != 200:
            logger.error(
                f"Bale deleteMessage error {response.status_code}: "
                f"{response.text[:200]}"
            )
            return False
        data = response.json()
        return bool(data.get("ok", True))
    except Exception as e:
        logger.error(f"Failed to delete Bale message {message_id} in {chat_id}: {e}")
        return False


def send_to_groups(text: str) -> int:
    """Send message to all configured groups. Returns count of successful sends."""
    sent = 0
    for group_id in BALE_GROUP_IDS:
        if send_bale_message(group_id, text):
            sent += 1
    return sent


def send_to_groups_with_ids(text: str) -> list:
    """Send to groups; return list of {chat_id, message_id, target_type}."""
    deliveries = []
    for group_id in BALE_GROUP_IDS:
        mid = send_bale_message(group_id, text)
        if mid is not None:
            deliveries.append({
                "chat_id": group_id,
                "message_id": mid,
                "target_type": "group",
            })
    return deliveries


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


def broadcast_dashboard_message(
    text: str,
    message_type: str = "admin",
    user_bale_ids: Optional[list] = None,
    send_to_users: bool = True,
    send_to_group: bool = True,
) -> dict:
    """
    Broadcast a message written in the web dashboard to users and/or groups.
    Returns counts plus deliveries [{chat_id, message_id, target_type}, ...].
    """
    formatted = MessageFormatter.format_broadcast_message(text, message_type)
    users_ok = 0
    users_fail = 0
    groups_ok = 0
    deliveries = []

    if send_to_users and user_bale_ids:
        for bale_id in user_bale_ids:
            mid = send_bale_message(bale_id, formatted)
            if mid is not None:
                users_ok += 1
                deliveries.append({
                    "chat_id": bale_id,
                    "message_id": mid,
                    "target_type": "user",
                })
            else:
                users_fail += 1

    if send_to_group:
        group_deliveries = send_to_groups_with_ids(formatted)
        groups_ok = len(group_deliveries)
        deliveries.extend(group_deliveries)

    logger.info(
        f"Dashboard broadcast ({message_type}): "
        f"users={users_ok}/{users_ok + users_fail}, groups={groups_ok}"
    )
    return {
        "formatted": formatted,
        "users_ok": users_ok,
        "users_fail": users_fail,
        "groups_ok": groups_ok,
        "deliveries": deliveries,
    }


def delete_broadcast_deliveries(deliveries: list) -> dict:
    """
    Delete previously sent broadcast messages from Bale.
    deliveries: list of dicts with chat_id, message_id (and optional id).
    """
    deleted = 0
    failed = 0
    deleted_ids = []
    for d in deliveries:
        chat_id = d.get("chat_id")
        message_id = d.get("message_id")
        if chat_id is None or message_id is None:
            failed += 1
            continue
        if delete_bale_message(int(chat_id), int(message_id)):
            deleted += 1
            if d.get("id") is not None:
                deleted_ids.append(d["id"])
        else:
            failed += 1
    return {"deleted": deleted, "failed": failed, "deleted_ids": deleted_ids}


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
