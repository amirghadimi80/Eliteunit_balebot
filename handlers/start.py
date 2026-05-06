"""
Start handler for /start command and user registration.
"""

import logging
import re
from balethon import Client
from balethon.objects import Message, InlineKeyboard, InlineKeyboardButton

from database.db import Database
from models.models import User
from config.settings import BUTTON_LABELS, MESSAGES

logger = logging.getLogger(__name__)

PHONE_PATTERN = re.compile(r"^(\+98|0098|98|0)?9\d{9}$")


class StartHandler:
    """Handler for /start command and user registration flow."""
    
    def __init__(self, db: Database):
        """
        Initialize start handler.
        
        Args:
            db: Database instance
        """
        self.db = db
        self.user_states = {}  # Track user registration state
    
    async def handle_start(self, client: Client, message: Message):
        """
        Handle /start command.
        Initiates user registration if new user.
        
        Args:
            client: Balethon client instance
            message: Message object from user
        """
        user_bale_id = message.chat.id
        
        # Check if user already registered
        existing_user = self.db.get_user_by_bale_id(user_bale_id)
        
        if existing_user:
            # User already registered, show main menu
            await self._show_main_menu(client, message)
        else:
            # New user, start registration
            await self._start_registration(client, message)
    
    async def _start_registration(self, client: Client, message: Message):
        """
        Start user registration process.
        
        Args:
            client: Balethon client instance
            message: Message object
        """
        user_id = message.chat.id
        
        # Set user state to waiting for name
        self.user_states[user_id] = {"state": "waiting_name"}
        
        # Send welcome message
        welcome_msg = (
            f"خوش آمدید به سیستم مدیریت زمان EliteUniteTime! 🎉\n\n"
            f"لطفاً اطلاعات خود را کامل کنید.\n\n"
            f"🔤 لطفاً نام کامل خود را وارد کنید:"
        )
        
        await client.send_message(
            chat_id=user_id,
            text=welcome_msg,
        )
    
    async def handle_name_input(self, client: Client, message: Message):
        """
        Handle user name input.
        
        Args:
            client: Balethon client instance
            message: Message object
        """
        user_id = message.chat.id
        full_name = message.text.strip()
        
        if not full_name or len(full_name) < 2:
            await client.send_message(
                chat_id=user_id,
                text="❌ نام نامعتبر است. لطفاً نام بیشتر از 2 حرف وارد کنید:",
            )
            return
        
        # Update user state
        self.user_states[user_id] = {
            "state": "waiting_phone",
            "full_name": full_name,
        }
        
        # Ask for phone number - try ReplyKeyboard with request_contact
        # Bale supports ReplyKeyboardButton with request_contact for sharing contact
        try:
            from balethon.objects import ReplyKeyboard, ReplyKeyboardButton
            keyboard = ReplyKeyboard(
                resize=True,
                one_time=True,
            )
            keyboard.add_row(
                ReplyKeyboardButton(
                    text="📞 اشتراک گذاری شماره",
                    request_contact=True,
                )
            )
            await client.send_message(
                chat_id=user_id,
                text="📞 لطفاً شماره تماس خود را اشتراک گذاری کنید\nیا شماره را به صورت دستی وارد کنید (مثال: 09123456789):",
                reply_markup=keyboard,
            )
        except Exception:
            # Fallback: ask user to type phone number manually
            await client.send_message(
                chat_id=user_id,
                text="📞 لطفاً شماره تماس خود را وارد کنید (مثال: 09123456789):",
            )
    
    async def handle_phone_input(self, client: Client, message: Message):
        """
        Handle phone contact sharing or manual phone number input.
        
        Args:
            client: Balethon client instance
            message: Message object
        """
        user_id = message.chat.id
        
        # Get phone from contact share or manual text input
        if message.contact:
            phone = message.contact.phone_number
            # Normalize phone number
            if phone and not phone.startswith("+"):
                phone = "+" + phone
        elif message.text:
            raw = message.text.strip()
            if PHONE_PATTERN.match(raw):
                # Normalize to +98 format
                digits = re.sub(r"^\+98|^0098|^98|^0", "", raw)
                phone = "+98" + digits
            else:
                await client.send_message(
                    chat_id=user_id,
                    text="❌ شماره تماس نامعتبر است.\nلطفاً شماره را به فرمت صحیح وارد کنید (مثال: 09123456789):",
                )
                return
        else:
            await client.send_message(
                chat_id=user_id,
                text="❌ لطفاً شماره تماس خود را وارد کنید (مثال: 09123456789):",
            )
            return
        
        # Get user data from state
        user_data = self.user_states.get(user_id)
        if not user_data or user_data.get("state") != "waiting_phone":
            await client.send_message(
                chat_id=user_id,
                text="❌ خطا در ثبت نام. لطفاً دوباره /start را بزنید.",
            )
            return
        
        # Create user
        user = User(
            bale_id=user_id,
            full_name=user_data.get("full_name"),
            phone=phone,
        )
        
        user_id_db = self.db.add_user(user)
        
        if user_id_db:
            # Clear user state
            del self.user_states[user_id]
            
            # Remove reply keyboard and send confirmation
            try:
                from balethon.objects import ReplyKeyboard
                await client.send_message(
                    chat_id=user_id,
                    text="✅ ثبت نام شما با موفقیت انجام شد!\n\nمنوی اصلی:",
                    reply_markup=ReplyKeyboard(remove=True),
                )
            except Exception:
                await client.send_message(
                    chat_id=user_id,
                    text="✅ ثبت نام شما با موفقیت انجام شد!\n\nمنوی اصلی:",
                )
            
            await self._show_main_menu(client, message)
            logger.info(f"User registered: {user.full_name} (ID: {user_id})")
        else:
            await client.send_message(
                chat_id=user_id,
                text="❌ خطا در ثبت نام. لطفاً دوباره تلاش کنید.",
            )
    
    async def _show_main_menu(self, client: Client, message: Message):
        """
        Show main menu buttons.
        
        Args:
            client: Balethon client instance
            message: Message object
        """
        user_id = message.chat.id
        
        # Create main menu keyboard
        keyboard = InlineKeyboard()
        
        # Daily report button
        keyboard.add_row(
            InlineKeyboardButton(
                text=BUTTON_LABELS.get("daily_report", "📊 گزارش روزانه"),
                callback_data="daily_report",
            )
        )
        
        # Weekly and Monthly report buttons in same row
        keyboard.add_row(
            InlineKeyboardButton(
                text=BUTTON_LABELS.get("weekly_report", "📈 گزارش هفتگی"),
                callback_data="weekly_report",
            ),
            InlineKeyboardButton(
                text=BUTTON_LABELS.get("monthly_report", "📅 گزارش ماهانه"),
                callback_data="monthly_report",
            )
        )
        
        # Profile button
        keyboard.add_row(
            InlineKeyboardButton(
                text=BUTTON_LABELS.get("profile", "👤 پروفایل من"),
                callback_data="profile",
            )
        )
        
        # Friends discovery button
        keyboard.add_row(
            InlineKeyboardButton(
                text=BUTTON_LABELS.get("friends", "👥 آشنایی با دوستان"),
                callback_data="friends",
            )
        )
        
        await client.send_message(
            chat_id=user_id,
            text="📋 منوی اصلی:",
            reply_markup=keyboard,
        )
