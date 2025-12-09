"""
Interactive Button Layouts for PnProjects Audio Bot
Beautiful and user-friendly inline keyboard interfaces
"""

from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import Config


class Buttons:
    """Centralized button layout management"""

    @staticmethod
    def start_menu():
        """Main start menu buttons"""
        return InlineKeyboardMarkup([
            [
                InlineKeyboardButton("🎵 Start Converting", callback_data="how_to_use"),
                InlineKeyboardButton("❓ Help", callback_data="help_main")
            ],
            [
                InlineKeyboardButton("⚡ Features", callback_data="features"),
                InlineKeyboardButton("📋 Formats", callback_data="supported_formats")
            ],
            [
                InlineKeyboardButton("👨‍💻 Developer", url="https://t.me/PnProjects")
            ]
        ])

    @staticmethod
    def help_menu():
        """Help menu with command categories"""
        return InlineKeyboardMarkup([
            [
                InlineKeyboardButton("📖 Commands", callback_data="help_commands"),
                InlineKeyboardButton("🎛️ Features", callback_data="help_features")
            ],
            [
                InlineKeyboardButton("🔧 Settings", callback_data="help_settings"),
                InlineKeyboardButton("📊 Formats", callback_data="help_formats")
            ],
            [
                InlineKeyboardButton("💡 Examples", callback_data="help_examples"),
                InlineKeyboardButton("❓ FAQ", callback_data="help_faq")
            ],
            [
                InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")
            ]
        ])

    @staticmethod
    def back_to_help():
        """Back to help button"""
        return InlineKeyboardMarkup([
            [InlineKeyboardButton("◀️ Back to Help", callback_data="help_main")]
        ])

    @staticmethod
    def format_selection():
        """Format selection menu"""
        return InlineKeyboardMarkup([
            [
                InlineKeyboardButton("🎵 MP3", callback_data="format_mp3"),
                InlineKeyboardButton("📀 M4A", callback_data="format_m4a"),
                InlineKeyboardButton("🎼 AAC", callback_data="format_aac")
            ],
            [
                InlineKeyboardButton("💎 FLAC", callback_data="format_flac"),
                InlineKeyboardButton("🌊 WAV", callback_data="format_wav"),
                InlineKeyboardButton("🎹 ALAC", callback_data="format_alac")
            ],
            [
                InlineKeyboardButton("🔊 OGG", callback_data="format_ogg"),
                InlineKeyboardButton("🎺 OPUS", callback_data="format_opus"),
                InlineKeyboardButton("🎸 WMA", callback_data="format_wma")
            ],
            [
                InlineKeyboardButton("📻 More Formats...", callback_data="format_more")
            ],
            [
                InlineKeyboardButton("❌ Cancel", callback_data="cancel_operation")
            ]
        ])

    @staticmethod
    def more_formats():
        """Additional format selection"""
        return InlineKeyboardMarkup([
            [
                InlineKeyboardButton("🎭 APE", callback_data="format_ape"),
                InlineKeyboardButton("🎪 WavPack", callback_data="format_wv"),
                InlineKeyboardButton("🎬 TTA", callback_data="format_tta")
            ],
            [
                InlineKeyboardButton("🎨 AIFF", callback_data="format_aiff"),
                InlineKeyboardButton("🎯 WebM", callback_data="format_webm"),
                InlineKeyboardButton("🎲 AC3", callback_data="format_ac3")
            ],
            [
                InlineKeyboardButton("◀️ Back", callback_data="select_format")
            ]
        ])

    @staticmethod
    def bitrate_selection():
        """Bitrate selection menu"""
        return InlineKeyboardMarkup([
            [
                InlineKeyboardButton("🔉 128k", callback_data="bitrate_128k"),
                InlineKeyboardButton("🔊 192k", callback_data="bitrate_192k"),
                InlineKeyboardButton("🔊 256k", callback_data="bitrate_256k")
            ],
            [
                InlineKeyboardButton("🔊 320k (Best)", callback_data="bitrate_320k"),
                InlineKeyboardButton("💎 500k", callback_data="bitrate_500k")
            ],
            [
                InlineKeyboardButton("✏️ Custom", callback_data="bitrate_custom"),
                InlineKeyboardButton("❌ Cancel", callback_data="cancel_operation")
            ]
        ])

    @staticmethod
    def sample_rate_selection():
        """Sample rate selection menu"""
        return InlineKeyboardMarkup([
            [
                InlineKeyboardButton("📻 22.05 kHz", callback_data="sample_22050"),
                InlineKeyboardButton("📻 44.1 kHz (CD)", callback_data="sample_44100")
            ],
            [
                InlineKeyboardButton("📻 48 kHz (Pro)", callback_data="sample_48000"),
                InlineKeyboardButton("💎 96 kHz (Hi-Res)", callback_data="sample_96000")
            ],
            [
                InlineKeyboardButton("💎 192 kHz (Studio)", callback_data="sample_192000")
            ],
            [
                InlineKeyboardButton("✏️ Custom", callback_data="sample_custom"),
                InlineKeyboardButton("❌ Cancel", callback_data="cancel_operation")
            ]
        ])

    @staticmethod
    def channel_selection():
        """Audio channel selection menu"""
        return InlineKeyboardMarkup([
            [
                InlineKeyboardButton("🔈 Mono (1)", callback_data="channels_1"),
                InlineKeyboardButton("🔊 Stereo (2)", callback_data="channels_2")
            ],
            [
                InlineKeyboardButton("🎭 5.1 Surround", callback_data="channels_6"),
                InlineKeyboardButton("🎪 7.1 Surround", callback_data="channels_8")
            ],
            [
                InlineKeyboardButton("❌ Cancel", callback_data="cancel_operation")
            ]
        ])

    @staticmethod
    def bass_boost_selection():
        """Bass boost level selection"""
        return InlineKeyboardMarkup([
            [
                InlineKeyboardButton("🔊 +1 dB", callback_data="bass_1"),
                InlineKeyboardButton("🔊 +2 dB", callback_data="bass_2"),
                InlineKeyboardButton("🔊 +3 dB", callback_data="bass_3")
            ],
            [
                InlineKeyboardButton("🔊 +4 dB", callback_data="bass_4"),
                InlineKeyboardButton("🔊 +5 dB (Max)", callback_data="bass_5")
            ],
            [
                InlineKeyboardButton("❌ Cancel", callback_data="cancel_operation")
            ]
        ])

    @staticmethod
    def audio_effects_menu():
        """Audio effects and enhancement menu"""
        return InlineKeyboardMarkup([
            [
                InlineKeyboardButton("🎚️ Bass Boost", callback_data="effect_bass_boost"),
                InlineKeyboardButton("🎼 Normalize", callback_data="effect_normalize")
            ],
            [
                InlineKeyboardButton("🎵 Fade In", callback_data="effect_fade_in"),
                InlineKeyboardButton("🎶 Fade Out", callback_data="effect_fade_out")
            ],
            [
                InlineKeyboardButton("⏩ Speed Up", callback_data="effect_speed_up"),
                InlineKeyboardButton("⏪ Speed Down", callback_data="effect_speed_down")
            ],
            [
                InlineKeyboardButton("🎹 Reverse", callback_data="effect_reverse"),
                InlineKeyboardButton("🔁 Loop", callback_data="effect_loop")
            ],
            [
                InlineKeyboardButton("◀️ Back", callback_data="main_menu")
            ]
        ])

    @staticmethod
    def processing_options(user_id: int):
        """Processing options for uploaded audio"""
        return InlineKeyboardMarkup([
            [
                InlineKeyboardButton("🔄 Convert Format", callback_data=f"process_convert_{user_id}"),
                InlineKeyboardButton("🎚️ Change Bitrate", callback_data=f"process_bitrate_{user_id}")
            ],
            [
                InlineKeyboardButton("📊 Sample Rate", callback_data=f"process_sample_{user_id}"),
                InlineKeyboardButton("🔊 Channels", callback_data=f"process_channels_{user_id}")
            ],
            [
                InlineKeyboardButton("🎵 Bass Boost", callback_data=f"process_bass_{user_id}"),
                InlineKeyboardButton("✨ Effects", callback_data=f"process_effects_{user_id}")
            ],
            [
                InlineKeyboardButton("⚙️ Advanced", callback_data=f"process_advanced_{user_id}"),
                InlineKeyboardButton("📋 Info Only", callback_data=f"process_info_{user_id}")
            ],
            [
                InlineKeyboardButton("❌ Cancel", callback_data="cancel_operation")
            ]
        ])

    @staticmethod
    def confirm_processing():
        """Confirmation buttons for processing"""
        return InlineKeyboardMarkup([
            [
                InlineKeyboardButton("✅ Confirm & Process", callback_data="confirm_process"),
                InlineKeyboardButton("❌ Cancel", callback_data="cancel_operation")
            ]
        ])

    @staticmethod
    def cancel_button():
        """Simple cancel button"""
        return InlineKeyboardMarkup([
            [InlineKeyboardButton("❌ Cancel", callback_data="cancel_operation")]
        ])

    @staticmethod
    def back_to_main():
        """Back to main menu button"""
        return InlineKeyboardMarkup([
            [InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")]
        ])


class HelpTexts:
    """Help text content for different sections"""

    COMMANDS = """
**📖 Available Commands**

**Basic Commands:**
/start - Start the bot and see welcome message
/help - Display this help menu
/cancel - Cancel current operation

**Quick Actions:**
/convert - Start audio conversion
/formats - View supported formats
/settings - View current settings

**Information:**
/info - Get audio file information
/about - About this bot

**How to Use:**
Simply send any audio file to the bot, and you'll get interactive buttons to choose what you want to do with it!
"""

    FEATURES = """
**🎛️ Bot Features**

**Format Conversion:**
✓ Convert between 20+ audio formats
✓ Support for both lossy and lossless formats
✓ High-quality codec support

**Audio Processing:**
✓ Adjust bitrate (128k to 500k+)
✓ Change sample rate (up to 192kHz)
✓ Modify audio channels (Mono to 7.1)
✓ Bass boost (1-5 dB)

**Effects & Enhancement:**
✓ Audio normalization
✓ Fade in/out effects
✓ Speed adjustment
✓ Reverse audio
✓ Loop audio

**Advanced:**
✓ Metadata editing
✓ Audio trimming
✓ Batch processing support
✓ Custom codec parameters
"""

    SETTINGS = """
**🔧 Audio Settings Guide**

**Bitrate:**
- 128k: Good for speech/podcasts
- 192k: Standard quality
- 256k: High quality
- 320k: Premium quality (recommended)
- 500k+: Audiophile quality

**Sample Rate:**
- 22.05 kHz: Voice recordings
- 44.1 kHz: CD quality (standard)
- 48 kHz: Professional audio
- 96 kHz: Hi-Res audio
- 192 kHz: Studio master quality

**Channels:**
- Mono (1): Single channel
- Stereo (2): Standard music
- 5.1: Surround sound
- 7.1: Full surround sound
"""

    FORMATS = """
**📊 Supported Audio Formats**

**Lossy Formats (Compressed):**
• MP3 - Most common format
• M4A/AAC - High quality, small size
• OGG Vorbis - Open source
• OPUS - Best quality/size ratio
• WMA - Windows Media Audio

**Lossless Formats (Uncompressed):**
• FLAC - Popular lossless format
• WAV - Standard uncompressed
• ALAC - Apple Lossless
• APE - Monkey's Audio
• WavPack - Hybrid compression
• TTA - True Audio
• AIFF - Audio Interchange Format

**Other Formats:**
• WebM Audio - Web format
• AC3 - Dolby Digital
• DTS - Surround sound
• And many more!
"""

    EXAMPLES = """
**💡 Usage Examples**

**Example 1: Convert to MP3**
1. Send your audio file
2. Click "Convert Format"
3. Select "MP3"
4. Choose bitrate (320k recommended)
5. Click "Process"

**Example 2: Enhance Bass**
1. Send your audio file
2. Click "Bass Boost"
3. Select boost level (2-3 dB recommended)
4. Confirm and wait for processing

**Example 3: Change Sample Rate**
1. Send your audio file
2. Click "Sample Rate"
3. Select desired rate (48kHz for pro audio)
4. Process and download

**Example 4: Advanced Processing**
1. Send audio file
2. Click "Advanced"
3. Customize multiple parameters
4. Preview settings
5. Process
"""

    FAQ = """
**❓ Frequently Asked Questions**

**Q: What's the maximum file size?**
A: Up to 2GB per file.

**Q: How long does processing take?**
A: Usually 10-60 seconds depending on file size and operation.

**Q: Do you store my files?**
A: No, files are deleted immediately after processing.

**Q: What's the best format for quality?**
A: FLAC for lossless, MP3 320k for lossy.

**Q: Can I convert multiple files?**
A: Yes, send files one by one.

**Q: Why use bass boost?**
A: Enhances low frequencies for better depth.

**Q: What's the difference between bitrate and sample rate?**
A: Bitrate affects quality/size, sample rate affects frequency range.

**Q: Is the bot free?**
A: Yes, completely free to use!
"""

    HOW_TO_USE = """
**🎵 How to Use This Bot**

**Step 1: Send Audio File**
Send any audio file (up to 2GB) to the bot.

**Step 2: Choose Operation**
Select what you want to do:
• Convert to different format
• Adjust audio quality
• Apply effects
• Get file information

**Step 3: Configure Settings**
Use interactive buttons to:
• Select output format
• Choose bitrate & sample rate
• Set audio channels
• Add effects

**Step 4: Process**
Confirm your settings and let the bot process your file.

**Step 5: Download**
Receive your processed audio file!

**Tips:**
✓ Use 320k bitrate for best MP3 quality
✓ Choose FLAC for lossless quality
✓ Try 2-3 dB bass boost for music
✓ 48kHz sample rate is great for most uses
"""
