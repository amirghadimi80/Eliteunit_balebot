"""
User profile and social discovery handler.
"""

import logging
from balethon import Client
from balethon.objects import Message, InlineKeyboard, InlineKeyboardButton

from database.db import Database
from utils.formatter import MessageFormatter

logger = logging.getLogger(__name__)


class ProfileHandler:
    """Handler for user profile and social discovery features."""
    
    def __init__(self, db: Database):
        """
        Initialize profile handler.
        
        Args:
            db: Database instance
        """
        self.db = db
        self.user_states = {}
    
    async def handle_profile_view(self, client: Client, message: Message):
        """
        Display user's own profile.
        
        Args:
            client: Balethon client instance
            message: Message object
        """
        user_id = message.chat.id
        user = self.db.get_user_by_bale_id(user_id)
        
        if not user:
            await client.send_message(
                chat_id=user_id,
                text="❌ لطفاً ابتدا ثبت نام کنید.",
            )
            return
        
        # Format profile message
        profile_msg = MessageFormatter.format_user_profile(
            user.full_name,
            phone=user.phone,
            bio=user.bio,
            interests=user.interests,
        )
        
        # Create edit button
        keyboard = InlineKeyboard()
        keyboard.add_row(
            InlineKeyboardButton(
                text="✏️ ویرایش پروفایل",
                callback_data="edit_profile",
            )
        )
        keyboard.add_row(
            InlineKeyboardButton(
                text="🏠 بازگشت به منوی اصلی",
                callback_data="main_menu",
            )
        )
        
        await client.send_message(
            chat_id=user_id,
            text=profile_msg,
            reply_markup=keyboard,
        )
    
    async def handle_edit_profile(self, client: Client, message: Message):
        """
        Start profile editing flow.
        
        Args:
            client: Balethon client instance
            message: Message object
        """
        user_id = message.chat.id
        
        self.user_states[user_id] = {
            "state": "edit_menu",
        }
        
        # Show edit options
        keyboard = InlineKeyboard()
        keyboard.add_row(
            InlineKeyboardButton(
                text="📝 ویرایش بیوگرافی",
                callback_data="edit_bio",
            )
        )
        keyboard.add_row(
            InlineKeyboardButton(
                text="⭐ ویرایش علاقه‌مندی‌ها",
                callback_data="edit_interests",
            )
        )
        keyboard.add_row(
            InlineKeyboardButton(
                text="🔙 بازگشت به پروفایل",
                callback_data="profile",
            )
        )
        keyboard.add_row(
            InlineKeyboardButton(
                text="🏠 بازگشت به منوی اصلی",
                callback_data="main_menu",
            )
        )
        
        await client.send_message(
            chat_id=user_id,
            text="📝 چه چیزی را ویرایش کنید؟",
            reply_markup=keyboard,
        )
    
    async def handle_edit_bio(self, client: Client, message: Message):
        """
        Handle bio editing.
        
        Args:
            client: Balethon client instance
            message: Message object
        """
        user_id = message.chat.id
        
        self.user_states[user_id] = {
            "state": "waiting_bio",
        }
        
        await client.send_message(
            chat_id=user_id,
            text="📝 بیوگرافی خود را وارد کنید:",
        )
    
    async def handle_bio_input(self, client: Client, message: Message):
        """
        Process bio input.
        
        Args:
            client: Balethon client instance
            message: Message object
        """
        user_id = message.chat.id
        user_data = self.user_states.get(user_id)
        
        if not user_data or user_data.get("state") != "waiting_bio":
            return
        
        bio = message.text.strip()
        user = self.db.get_user_by_bale_id(user_id)
        
        if user:
            user.bio = bio
            if self.db.update_user(user):
                await client.send_message(
                    chat_id=user_id,
                    text="✅ بیوگرافی بروزرسانی شد!",
                )
                del self.user_states[user_id]
                logger.info(f"User bio updated: {user.full_name}")
            else:
                await client.send_message(
                    chat_id=user_id,
                    text="❌ خطا در بروزرسانی.",
                )
    
    async def handle_edit_interests(self, client: Client, message: Message):
        """
        Handle interests editing.
        
        Args:
            client: Balethon client instance
            message: Message object
        """
        user_id = message.chat.id
        
        self.user_states[user_id] = {
            "state": "waiting_interests",
        }
        
        await client.send_message(
            chat_id=user_id,
            text="⭐ علاقه‌مندی‌های خود را وارد کنید:\n(مثال: ورزش، برنامه‌نویسی، موسیقی)",
        )
    
    async def handle_interests_input(self, client: Client, message: Message):
        """
        Process interests input.
        
        Args:
            client: Balethon client instance
            message: Message object
        """
        user_id = message.chat.id
        user_data = self.user_states.get(user_id)
        
        if not user_data or user_data.get("state") != "waiting_interests":
            return
        
        interests = message.text.strip()
        user = self.db.get_user_by_bale_id(user_id)
        
        if user:
            user.interests = interests
            if self.db.update_user(user):
                await client.send_message(
                    chat_id=user_id,
                    text="✅ علاقه‌مندی‌ها بروزرسانی شد!",
                )
                del self.user_states[user_id]
                logger.info(f"User interests updated: {user.full_name}")
            else:
                await client.send_message(
                    chat_id=user_id,
                    text="❌ خطا در بروزرسانی.",
                )
    
    async def handle_friends_discovery(self, client: Client, message: Message):
        """
        Show list of users for social discovery.
        
        Args:
            client: Balethon client instance
            message: Message object
        """
        user_id = message.chat.id
        user = self.db.get_user_by_bale_id(user_id)
        
        if not user:
            await client.send_message(
                chat_id=user_id,
                text="❌ لطفاً ابتدا ثبت نام کنید.",
            )
            return
        
        # Get all users except current user
        all_users = self.db.get_all_users()
        other_users = [u for u in all_users if u.bale_id != user_id and u.bio]
        
        if not other_users:
            await client.send_message(
                chat_id=user_id,
                text="👥 هیچ کاربری با پروفایل کامل وجود ندارد.",
            )
            return
        
        # Create buttons for each user
        keyboard = InlineKeyboard()
        for other_user in other_users[:10]:  # Limit to 10 for keyboard size
            keyboard.add_row(
                InlineKeyboardButton(
                    text=f"👤 {other_user.full_name}",
                    callback_data=f"view_user_{other_user.id}",
                )
            )
        
        await client.send_message(
            chat_id=user_id,
            text="👥 آشنایی با دوستان:\n\nکاربری را انتخاب کنید:",
            reply_markup=keyboard,
        )
    
    async def handle_view_user_profile(self, client: Client, message: Message, user_id_to_view: int):
        """
        Display another user's profile.
        
        Args:
            client: Balethon client instance
            message: Message object
            user_id_to_view: ID of user to view
        """
        user_to_view = self.db.get_user_by_id(user_id_to_view)
        
        if not user_to_view:
            await client.send_message(
                chat_id=message.chat.id,
                text="❌ کاربر یافت نشد.",
            )
            return
        
        # Format profile message
        profile_msg = MessageFormatter.format_user_profile(
            user_to_view.full_name,
            phone=None,  # Don't show phone to others
            bio=user_to_view.bio,
            interests=user_to_view.interests,
        )
        
        await client.send_message(
            chat_id=message.chat.id,
            text=profile_msg,
        )
