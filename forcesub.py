"""
Force Subscription Module for PnProjects Audio Bot
Enforces users to join a specific channel before using the bot
"""

import logging
from pyrogram import Client
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.enums import ChatMemberStatus
from pyrogram.errors import (
    UserNotParticipant,
    ChatAdminRequired,
    ChannelInvalid,
    ChannelPrivate,
    PeerIdInvalid,
)
from config import Config
from typing import Optional

logger = logging.getLogger(__name__)


class ForceSubscription:
    """Handles force subscription logic"""

    _resolved_channel_id: Optional[object] = None

    @staticmethod
    async def resolve_channel_id(client: Client) -> Optional[object]:
        """
        Resolve configured FORCE_SUB_CHANNEL to a usable chat identifier.
        Caches the result to avoid repeated lookups.
        """
        if ForceSubscription._resolved_channel_id is not None:
            return ForceSubscription._resolved_channel_id

        raw = Config.FORCE_SUB_CHANNEL
        if not raw:
            return None

        # Already numeric/int-like
        if isinstance(raw, int) or (isinstance(raw, str) and raw.lstrip("-").isdigit()):
            ForceSubscription._resolved_channel_id = raw
            return ForceSubscription._resolved_channel_id

        # Resolve usernames/links to chat id
        try:
            chat = await client.get_chat(raw)
            ForceSubscription._resolved_channel_id = chat.id
            logger.info(
                "ForceSub: resolved channel %s -> %s (type: %s)",
                raw,
                chat.id,
                type(chat.id).__name__,
            )
            return ForceSubscription._resolved_channel_id
        except Exception:
            logger.exception("ForceSub: failed to resolve channel %s", raw)
            ForceSubscription._resolved_channel_id = raw  # fallback to raw
            return ForceSubscription._resolved_channel_id

    @staticmethod
    async def get_invite_link(client: Client, channel_id: str) -> Optional[str]:
        """Get invite link for the channel"""
        try:
            # Use resolved channel id to avoid PeerIdInvalid
            resolved = await ForceSubscription.resolve_channel_id(client)
            chat = await client.get_chat(resolved or channel_id)
            if chat.invite_link:
                return chat.invite_link

            # Create invite link if bot is admin
            try:
                link = await client.create_chat_invite_link(channel_id)
                return link.invite_link
            except ChatAdminRequired:
                # If bot is not admin, try to get username
                if chat.username:
                    return f"https://t.me/{chat.username}"
                return None
        except Exception as e:
            logger.exception("Error getting invite link")
            return None

    @staticmethod
    async def is_user_subscribed(client: Client, user_id: int, channel_id: str) -> bool:
        """Check if user is subscribed to the channel"""
        if not Config.FORCE_SUB_CHANNEL:
            return True

        # Resolve to a usable id/username once
        channel_id = await ForceSubscription.resolve_channel_id(client)

        try:
            member = await client.get_chat_member(channel_id, user_id)
            status = getattr(member, "status", None)
            logger.info(
                "ForceSub: user %s status in %s is %s",
                user_id,
                channel_id,
                status,
            )

            allowed_statuses = {
                ChatMemberStatus.CREATOR,
                ChatMemberStatus.ADMINISTRATOR,
                ChatMemberStatus.MEMBER,
                ChatMemberStatus.RESTRICTED,
                # string fallbacks for older pyrogram/typing
                "creator",
                "administrator",
                "member",
                "restricted",
            }

            return status in allowed_statuses
        except UserNotParticipant:
            logger.info("ForceSub: user %s is not a participant of %s", user_id, channel_id)
            return False
        except PeerIdInvalid:
            # Misconfigured FORCE_SUB_CHANNEL (bad ID/URL). Allow user but warn.
            logger.error(
                "Error: FORCE_SUB_CHANNEL appears invalid. Use channel username or "
                "numeric ID with -100 prefix. Force-sub check skipped for this request."
            )
            return True
        except (ChannelInvalid, ChannelPrivate):
            logger.error("Error: Bot is not member of channel %s", channel_id)
            return True  # Allow user if channel is invalid
        except ChatAdminRequired:
            logger.error(
                "Error: Bot must be an admin in the force-sub channel to check members."
            )
            return True  # Don't block users if bot lacks admin rights
        except Exception as e:
            logger.exception("Error checking subscription for user %s in channel %s", user_id, channel_id)
            return True  # Allow user on error to prevent bot breaking

    @staticmethod
    async def handle_force_sub(client: Client, message: Message) -> bool:
        """
        Handle force subscription check
        Returns True if user is subscribed or force sub is disabled
        Returns False if user needs to subscribe
        """
        if not Config.FORCE_SUB_CHANNEL:
            return True

        user_id = message.from_user.id
        is_subscribed = await ForceSubscription.is_user_subscribed(
            client, user_id, Config.FORCE_SUB_CHANNEL
        )

        if not is_subscribed:
            invite_link = await ForceSubscription.get_invite_link(
                client, Config.FORCE_SUB_CHANNEL
            )

            buttons = []
            if invite_link:
                buttons.append([
                    InlineKeyboardButton("🔔 Join Channel", url=invite_link)
                ])
            buttons.append([
                InlineKeyboardButton("✅ Check Subscription", callback_data="check_sub")
            ])

            await message.reply_text(
                "**🔒 Access Restricted!**\n\n"
                "You must join our channel to use this bot.\n\n"
                "**Steps:**\n"
                "1️⃣ Click the 'Join Channel' button below\n"
                "2️⃣ Join the channel\n"
                "3️⃣ Click 'Check Subscription' to verify\n\n"
                "After joining, you'll have full access to all features!",
                reply_markup=InlineKeyboardMarkup(buttons)
            )
            return False

        return True

    @staticmethod
    async def handle_check_subscription(client: Client, callback_query):
        """Handle the check subscription callback"""
        if not Config.FORCE_SUB_CHANNEL:
            await callback_query.answer("No subscription required!", show_alert=True)
            return

        channel_id = Config.FORCE_SUB_CHANNEL
        user_id = callback_query.from_user.id
        is_subscribed = await ForceSubscription.is_user_subscribed(client, user_id, channel_id)

        if is_subscribed:
            await callback_query.answer("✅ Subscription verified!", show_alert=True)
            await callback_query.message.delete()
            await callback_query.message.reply_text(
                "**✅ Subscription Verified!**\n\n"
                "You can now use all bot features.\n"
                "Send /start to begin or /help for available commands.",
            )
        else:
            await callback_query.answer(
                "❌ You haven't joined the channel yet. Please join and try again.",
                show_alert=True
            )
            logger.info(
                "ForceSub: user %s failed check for channel %s (force_sub configured)",
                user_id,
                channel_id,
            )
