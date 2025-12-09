"""
Main Bot Logic for PnProjects Audio Bot
Advanced audio processing with state-of-the-art features
"""

import os
import asyncio
import logging
from datetime import datetime
from typing import Dict, Optional
import subprocess
import json

from pyrogram import filters
from pyrogram.types import Message, CallbackQuery
from pyrogram.errors import MessageNotModified

from client import PnProjects
from config import Config
from buttons import Buttons, HelpTexts
from forcesub import ForceSubscription

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Initialize bot
bot = PnProjects()

# User session storage (in-memory, no database)
user_sessions: Dict[int, Dict] = {}


class AudioProcessor:
    """Advanced audio processing using FFmpeg and industry-standard tools"""

    @staticmethod
    async def get_audio_info(file_path: str) -> Dict:
        """Extract detailed audio information using FFprobe"""
        try:
            cmd = [
                'ffprobe', '-v', 'quiet', '-print_format', 'json',
                '-show_format', '-show_streams', file_path
            ]
            result = subprocess.run(cmd, capture_output=True, text=True)
            data = json.loads(result.stdout)

            audio_stream = next(
                (s for s in data.get('streams', []) if s['codec_type'] == 'audio'),
                {}
            )

            format_info = data.get('format', {})

            return {
                'codec': audio_stream.get('codec_name', 'unknown'),
                'bitrate': int(audio_stream.get('bit_rate', 0)) // 1000 if audio_stream.get('bit_rate') else 0,
                'sample_rate': int(audio_stream.get('sample_rate', 0)),
                'channels': audio_stream.get('channels', 0),
                'duration': float(format_info.get('duration', 0)),
                'size': int(format_info.get('size', 0)),
                'format': format_info.get('format_name', 'unknown')
            }
        except Exception as e:
            logger.exception("Error getting audio info")
            return {}

    @staticmethod
    async def convert_audio(
        input_file: str,
        output_file: str,
        output_format: str = 'mp3',
        bitrate: str = '320k',
        sample_rate: int = 48000,
        channels: int = 2,
        bass_boost: int = 0,
        normalize: bool = False,
        fade_in: float = 0,
        fade_out: float = 0,
        speed: float = 1.0,
        reverse: bool = False,
        custom_filters: Optional[str] = None
    ) -> bool:
        """
        Advanced audio conversion with multiple parameters
        Uses FFmpeg with optimized settings
        """
        try:
            # Build FFmpeg command
            cmd = ['ffmpeg', '-i', input_file, '-y']

            # Audio filters
            filters = []

            # Bass boost using equalizer
            if bass_boost > 0:
                filters.append(f'equalizer=f=100:width_type=h:width=200:g={bass_boost}')

            # Normalize audio
            if normalize:
                filters.append('loudnorm=I=-16:TP=-1.5:LRA=11')

            # Fade effects
            if fade_in > 0:
                filters.append(f'afade=t=in:st=0:d={fade_in}')
            if fade_out > 0:
                # Get duration for fade out
                info = await AudioProcessor.get_audio_info(input_file)
                duration = info.get('duration', 0)
                if duration > 0:
                    filters.append(f'afade=t=out:st={duration - fade_out}:d={fade_out}')

            # Speed adjustment
            if speed != 1.0:
                filters.append(f'atempo={speed}')

            # Reverse audio
            if reverse:
                filters.append('areverse')

            # Custom filters
            if custom_filters:
                filters.append(custom_filters)

            # Apply filters
            if filters:
                cmd.extend(['-af', ','.join(filters)])

            # Codec selection based on format
            codec_map = {
                'mp3': 'libmp3lame',
                'm4a': 'aac',
                'aac': 'aac',
                'ogg': 'libvorbis',
                'opus': 'libopus',
                'flac': 'flac',
                'wav': 'pcm_s16le',
                'alac': 'alac',
                'wma': 'wmav2',
                'ac3': 'ac3',
                'webm': 'libopus'
            }

            codec = codec_map.get(output_format.lower(), 'copy')

            # Set codec
            if codec != 'copy':
                cmd.extend(['-c:a', codec])

            # Set bitrate (not for lossless)
            lossless_formats = ['flac', 'wav', 'alac', 'ape', 'wv', 'tta', 'aiff']
            if output_format.lower() not in lossless_formats:
                cmd.extend(['-b:a', bitrate])

            # Set sample rate
            cmd.extend(['-ar', str(sample_rate)])

            # Set channels
            cmd.extend(['-ac', str(channels)])

            # Quality settings
            if output_format.lower() == 'mp3':
                cmd.extend(['-q:a', '0'])  # VBR quality
            elif output_format.lower() in ['aac', 'm4a']:
                cmd.extend(['-movflags', '+faststart'])
            elif output_format.lower() == 'flac':
                cmd.extend(['-compression_level', '8'])

            # Output file
            cmd.append(output_file)

            # Execute conversion
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            await process.communicate()

            return process.returncode == 0

        except Exception as e:
            logger.exception("Error converting audio")
            return False

    @staticmethod
    def format_duration(seconds: float) -> str:
        """Format duration in human-readable format"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)

        if hours > 0:
            return f"{hours}h {minutes}m {secs}s"
        elif minutes > 0:
            return f"{minutes}m {secs}s"
        else:
            return f"{secs}s"

    @staticmethod
    def format_size(bytes_size: int) -> str:
        """Format file size in human-readable format"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if bytes_size < 1024.0:
                return f"{bytes_size:.2f} {unit}"
            bytes_size /= 1024.0
        return f"{bytes_size:.2f} TB"


async def cleanup_files(*file_paths):
    """Clean up temporary files"""
    for file_path in file_paths:
        try:
            if file_path and os.path.exists(file_path):
                os.remove(file_path)
                logger.info("Cleaned up: %s", file_path)
        except Exception:
            logger.exception("Error cleaning up %s", file_path)


def get_user_session(user_id: int) -> Dict:
    """Get or create user session"""
    if user_id not in user_sessions:
        user_sessions[user_id] = {
            'file_path': None,
            'file_info': None,
            'settings': {
                'format': 'mp3',
                'bitrate': '320k',
                'sample_rate': 48000,
                'channels': 2,
                'bass_boost': 0,
                'normalize': False,
                'fade_in': 0,
                'fade_out': 0,
                'speed': 1.0,
                'reverse': False
            }
        }
    return user_sessions[user_id]


def clear_user_session(user_id: int):
    """Clear user session data"""
    if user_id in user_sessions:
        session = user_sessions[user_id]
        if session.get('file_path'):
            asyncio.create_task(cleanup_files(session['file_path']))
        del user_sessions[user_id]


@bot.on_message(filters.command("start"))
async def start_command(client: PnProjects, message: Message):
    """Handle /start command"""
    if not await ForceSubscription.handle_force_sub(client, message):
        return

    welcome_text = f"""
**👋 Welcome to {Config.BOT_NAME}!**

Your ultimate audio processing companion with professional-grade features!

**🎯 What I Can Do:**
✓ Convert between 20+ audio formats
✓ Adjust quality, bitrate, and sample rate
✓ Enhance bass and apply effects
✓ Support for lossless formats
✓ Fast, async processing
✓ No file storage - your privacy matters

**🚀 Quick Start:**
Simply send me any audio file and I'll show you what I can do!

**Need Help?**
Click the buttons below to explore features and commands.
"""
    await message.reply_text(
        welcome_text,
        reply_markup=Buttons.start_menu()
    )


@bot.on_message(filters.command("help"))
async def help_command(client: PnProjects, message: Message):
    """Handle /help command"""
    if not await ForceSubscription.handle_force_sub(client, message):
        return

    await message.reply_text(
        "**📚 Help Center**\n\nChoose a topic to learn more:",
        reply_markup=Buttons.help_menu()
    )


@bot.on_message(filters.command("cancel"))
async def cancel_command(client: PnProjects, message: Message):
    """Handle /cancel command"""
    user_id = message.from_user.id
    clear_user_session(user_id)
    await message.reply_text("✅ Operation cancelled. All data cleared.")


@bot.on_message(filters.audio | filters.document | filters.voice)
async def handle_audio(client: PnProjects, message: Message):
    """Handle audio file uploads"""
    if not await ForceSubscription.handle_force_sub(client, message):
        return

    user_id = message.from_user.id
    status_msg = await message.reply_text("⏬ Downloading your audio file...")

    try:
        # Get file
        if message.audio:
            file = message.audio
        elif message.voice:
            file = message.voice
        elif message.document:
            file = message.document
        else:
            await status_msg.edit_text("❌ No audio file found!")
            return

        # Check file size
        if file.file_size > Config.MAX_FILE_SIZE:
            await status_msg.edit_text(
                f"❌ File too large! Maximum size: {AudioProcessor.format_size(Config.MAX_FILE_SIZE)}"
            )
            return

        # Download file
        timestamp = int(datetime.now().timestamp())
        file_ext = file.file_name.split('.')[-1] if hasattr(file, 'file_name') and file.file_name else 'audio'
        download_path = os.path.join(
            Config.DOWNLOAD_LOCATION,
            f"{user_id}_{timestamp}_input.{file_ext}"
        )

        file_path = await client.download_media(message, file_name=download_path)

        # Get audio info
        await status_msg.edit_text("📊 Analyzing audio file...")
        audio_info = await AudioProcessor.get_audio_info(file_path)

        # Store in session
        session = get_user_session(user_id)
        session['file_path'] = file_path
        session['file_info'] = audio_info

        # Send file info with options
        info_text = f"""
**📁 Audio File Received!**

**📊 File Information:**
📝 Format: `{audio_info.get('format', 'unknown').upper()}`
🎵 Codec: `{audio_info.get('codec', 'unknown').upper()}`
⚡ Bitrate: `{audio_info.get('bitrate', 0)} kbps`
📻 Sample Rate: `{audio_info.get('sample_rate', 0)} Hz`
🔊 Channels: `{audio_info.get('channels', 0)}`
⏱️ Duration: `{AudioProcessor.format_duration(audio_info.get('duration', 0))}`
💾 Size: `{AudioProcessor.format_size(audio_info.get('size', 0))}`

**What would you like to do?**
"""

        await status_msg.edit_text(
            info_text,
            reply_markup=Buttons.processing_options(user_id)
        )

    except Exception as e:
        logger.exception("Error handling audio")
        await status_msg.edit_text(f"❌ Error processing file: {str(e)}")
        clear_user_session(user_id)


@bot.on_callback_query()
async def handle_callbacks(client: PnProjects, callback_query: CallbackQuery):
    """Handle all callback queries"""
    data = callback_query.data
    user_id = callback_query.from_user.id

    # Check subscription for certain callbacks
    if data not in ["check_sub"] and not data.startswith("help_"):
        if not await ForceSubscription.handle_force_sub(client, callback_query.message):
            await callback_query.answer("Please join the channel first!", show_alert=True)
            return

    try:
        # Handle subscription check
        if data == "check_sub":
            await ForceSubscription.handle_check_subscription(client, callback_query)
            return

        # Main menu callbacks
        if data == "main_menu":
            await callback_query.message.edit_text(
                "**🏠 Main Menu**\n\nWhat would you like to do?",
                reply_markup=Buttons.start_menu()
            )

        elif data == "how_to_use":
            await callback_query.message.edit_text(
                HelpTexts.HOW_TO_USE,
                reply_markup=Buttons.back_to_main()
            )

        elif data == "features":
            await callback_query.message.edit_text(
                HelpTexts.FEATURES,
                reply_markup=Buttons.back_to_main()
            )

        elif data == "supported_formats":
            await callback_query.message.edit_text(
                HelpTexts.FORMATS,
                reply_markup=Buttons.back_to_main()
            )

        # Help menu callbacks
        elif data == "help_main":
            await callback_query.message.edit_text(
                "**📚 Help Center**\n\nChoose a topic:",
                reply_markup=Buttons.help_menu()
            )

        elif data == "help_commands":
            await callback_query.message.edit_text(
                HelpTexts.COMMANDS,
                reply_markup=Buttons.back_to_help()
            )

        elif data == "help_features":
            await callback_query.message.edit_text(
                HelpTexts.FEATURES,
                reply_markup=Buttons.back_to_help()
            )

        elif data == "help_settings":
            await callback_query.message.edit_text(
                HelpTexts.SETTINGS,
                reply_markup=Buttons.back_to_help()
            )

        elif data == "help_formats":
            await callback_query.message.edit_text(
                HelpTexts.FORMATS,
                reply_markup=Buttons.back_to_help()
            )

        elif data == "help_examples":
            await callback_query.message.edit_text(
                HelpTexts.EXAMPLES,
                reply_markup=Buttons.back_to_help()
            )

        elif data == "help_faq":
            await callback_query.message.edit_text(
                HelpTexts.FAQ,
                reply_markup=Buttons.back_to_help()
            )

        # Processing options
        elif data.startswith("process_convert_"):
            await callback_query.message.edit_text(
                "**🔄 Format Conversion**\n\nSelect output format:",
                reply_markup=Buttons.format_selection()
            )

        elif data.startswith("process_bitrate_"):
            await callback_query.message.edit_text(
                "**🎚️ Bitrate Selection**\n\nChoose bitrate quality:",
                reply_markup=Buttons.bitrate_selection()
            )

        elif data.startswith("process_sample_"):
            await callback_query.message.edit_text(
                "**📻 Sample Rate Selection**\n\nChoose sample rate:",
                reply_markup=Buttons.sample_rate_selection()
            )

        elif data.startswith("process_channels_"):
            await callback_query.message.edit_text(
                "**🔊 Channel Configuration**\n\nSelect audio channels:",
                reply_markup=Buttons.channel_selection()
            )

        elif data.startswith("process_bass_"):
            await callback_query.message.edit_text(
                "**🎚️ Bass Boost**\n\nSelect boost level:",
                reply_markup=Buttons.bass_boost_selection()
            )

        elif data.startswith("process_effects_"):
            await callback_query.message.edit_text(
                "**✨ Audio Effects**\n\nChoose an effect:",
                reply_markup=Buttons.audio_effects_menu()
            )

        elif data.startswith("process_info_"):
            session = get_user_session(user_id)
            info = session.get('file_info', {})
            settings = session.get('settings', {})

            info_text = f"""
**📊 Detailed Audio Information**

**Current File:**
📝 Format: `{info.get('format', 'unknown').upper()}`
🎵 Codec: `{info.get('codec', 'unknown').upper()}`
⚡ Bitrate: `{info.get('bitrate', 0)} kbps`
📻 Sample Rate: `{info.get('sample_rate', 0)} Hz`
🔊 Channels: `{info.get('channels', 0)}`
⏱️ Duration: `{AudioProcessor.format_duration(info.get('duration', 0))}`
💾 Size: `{AudioProcessor.format_size(info.get('size', 0))}`

**Current Settings:**
🔄 Output Format: `{settings.get('format', 'mp3').upper()}`
⚡ Bitrate: `{settings.get('bitrate', '320k')}`
📻 Sample Rate: `{settings.get('sample_rate', 48000)} Hz`
🔊 Channels: `{settings.get('channels', 2)}`
��️ Bass Boost: `{settings.get('bass_boost', 0)} dB`
"""
            await callback_query.message.edit_text(
                info_text,
                reply_markup=Buttons.processing_options(user_id)
            )

        # Format selection
        elif data.startswith("format_"):
            if data == "format_more":
                await callback_query.message.edit_text(
                    "**📋 More Formats**\n\nSelect format:",
                    reply_markup=Buttons.more_formats()
                )
            else:
                format_code = data.replace("format_", "")
                session = get_user_session(user_id)
                session['settings']['format'] = format_code

                await callback_query.answer(
                    f"✅ Format set to {format_code.upper()}",
                    show_alert=False
                )
                await callback_query.message.edit_text(
                    f"**✅ Format Selected: {Config.get_format_display_name(format_code)}**\n\n"
                    "Now choose bitrate:",
                    reply_markup=Buttons.bitrate_selection()
                )

        # Bitrate selection
        elif data.startswith("bitrate_"):
            bitrate = data.replace("bitrate_", "")
            session = get_user_session(user_id)
            session['settings']['bitrate'] = bitrate

            await callback_query.answer(f"✅ Bitrate set to {bitrate}", show_alert=False)
            await callback_query.message.edit_text(
                f"**⚙️ Settings Configured**\n\n"
                f"Format: `{session['settings']['format'].upper()}`\n"
                f"Bitrate: `{bitrate}`\n\n"
                "Ready to process?",
                reply_markup=Buttons.confirm_processing()
            )

        # Sample rate selection
        elif data.startswith("sample_"):
            sample = data.replace("sample_", "")
            session = get_user_session(user_id)
            session['settings']['sample_rate'] = int(sample)

            await callback_query.answer(f"✅ Sample rate set to {sample} Hz", show_alert=False)
            await callback_query.message.edit_text(
                "**✅ Sample Rate Updated**\n\nSelect channels:",
                reply_markup=Buttons.channel_selection()
            )

        # Channel selection
        elif data.startswith("channels_"):
            channels = int(data.replace("channels_", ""))
            session = get_user_session(user_id)
            session['settings']['channels'] = channels

            await callback_query.answer(f"✅ Channels set to {channels}", show_alert=False)
            await callback_query.message.edit_text(
                "**✅ Channels Configured**\n\nReady to process?",
                reply_markup=Buttons.confirm_processing()
            )

        # Bass boost selection
        elif data.startswith("bass_"):
            boost = int(data.replace("bass_", ""))
            session = get_user_session(user_id)
            session['settings']['bass_boost'] = boost

            await callback_query.answer(f"✅ Bass boost set to +{boost} dB", show_alert=False)
            await callback_query.message.edit_text(
                f"**✅ Bass Boost Applied: +{boost} dB**\n\nReady to process?",
                reply_markup=Buttons.confirm_processing()
            )

        # Confirm processing
        elif data == "confirm_process":
            await process_audio(client, callback_query)
            return

        # Cancel operation
        elif data == "cancel_operation":
            clear_user_session(user_id)
            await callback_query.message.edit_text(
                "❌ Operation cancelled.\n\nSend a new audio file to start again."
            )

        await callback_query.answer()

    except MessageNotModified:
        await callback_query.answer()
    except Exception as e:
        logger.exception("Error in callback")
        await callback_query.answer(f"Error: {str(e)}", show_alert=True)


async def process_audio(client: PnProjects, callback_query: CallbackQuery):
    """Process audio file with configured settings"""
    user_id = callback_query.from_user.id
    session = get_user_session(user_id)

    input_file = session.get('file_path')
    if not input_file or not os.path.exists(input_file):
        await callback_query.message.edit_text(
            "❌ File not found. Please send your audio file again."
        )
        clear_user_session(user_id)
        return

    settings = session['settings']
    output_format = settings['format']
    timestamp = int(datetime.now().timestamp())
    output_file = os.path.join(
        Config.DOWNLOAD_LOCATION,
        f"{user_id}_{timestamp}_output.{output_format}"
    )

    try:
        # Update status
        await callback_query.message.edit_text("⚙️ Processing audio... Please wait.")

        # Process audio
        success = await AudioProcessor.convert_audio(
            input_file=input_file,
            output_file=output_file,
            output_format=output_format,
            bitrate=settings['bitrate'],
            sample_rate=settings['sample_rate'],
            channels=settings['channels'],
            bass_boost=settings['bass_boost'],
            normalize=settings.get('normalize', False),
            fade_in=settings.get('fade_in', 0),
            fade_out=settings.get('fade_out', 0),
            speed=settings.get('speed', 1.0),
            reverse=settings.get('reverse', False)
        )

        if not success or not os.path.exists(output_file):
            await callback_query.message.edit_text(
                "❌ Processing failed. Please try again with different settings."
            )
            await cleanup_files(input_file, output_file)
            clear_user_session(user_id)
            return

        # Send processed file
        await callback_query.message.edit_text("⬆️ Uploading processed audio...")

        file_size = os.path.getsize(output_file)
        caption = f"""
**✅ Processing Complete!**

**Settings Used:**
🔄 Format: `{output_format.upper()}`
⚡ Bitrate: `{settings['bitrate']}`
📻 Sample Rate: `{settings['sample_rate']} Hz`
🔊 Channels: `{settings['channels']}`
💾 Size: `{AudioProcessor.format_size(file_size)}`
"""

        if settings['bass_boost'] > 0:
            caption += f"\n🎚️ Bass Boost: `+{settings['bass_boost']} dB`"

        await client.send_audio(
            chat_id=callback_query.message.chat.id,
            audio=output_file,
            caption=caption
        )

        await callback_query.message.edit_text(
            "✅ **Processing Complete!**\n\nYour file has been sent above.\n\n"
            "Send another audio file to convert more!"
        )

        # Cleanup
        await cleanup_files(input_file, output_file)
        clear_user_session(user_id)

    except Exception:
        logger.exception("Error processing audio")
        await callback_query.message.edit_text(f"❌ Error: {str(e)}")
        await cleanup_files(input_file, output_file)
        clear_user_session(user_id)


if __name__ == "__main__":
    logger.info("=" * 50)
    logger.info("Starting %s...", Config.BOT_NAME)
    logger.info("=" * 50)
    bot.run()
