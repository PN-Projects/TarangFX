"""UI builders for inline keyboards"""
from telethon import Button


LOSSY_BITRATE_OPTIONS = [128, 192, 256, 320]
# Curated high-bitrate presets for FLAC-like workflows (not exhaustive 1kbps steps).
LOSSLESS_BITRATE_OPTIONS = [
    128, 192, 256, 320,
    512, 768,
    1024, 1536, 2048,
    3072, 4096, 6144,
    8192, 12288, 16384,
    24576, 32768, 36000,
]


def _chunked(items, size):
    for i in range(0, len(items), size):
        yield items[i:i + size]

def get_status_text(session, is_premium: bool) -> str:
    """Generate status text with selected operations"""
    file_info = session.audio_file
    duration = file_info.get('duration', 0)
    size_mb = file_info.get('file_size', 0) / (1024**2)
    
    text = (
        f"✅ <b>Audio File Ready!</b>\n\n"
        f"📄 <code>{file_info.get('file_name', 'Unknown')}</code>\n"
        f"⏱️ Duration: {duration:.1f}s\n"
        f"💾 Size: {size_mb:.1f} MB\n"
        f"🎵 Format: {file_info.get('format', 'Unknown')}\n"
    )
    
    if session.operations:
        text += "\n<b>📋 Selected Operations:</b>\n"
        for i, op in enumerate(session.get_sorted_operations()):
            text += f"{i+1}. <b>{op.operation_type.title()}</b>: "
            # Add parameter details
            params = []
            for k, v in op.parameters.items():
                if k != 'extension': # Skip internal params
                    params.append(str(v))
            text += f"{', '.join(params)}\n"
            
        text += "\nSelect more operations or press <b>✅ Process</b>"
    else:
        text += "\nSelect operations below, then press <b>✅ Process</b>"
        
    return text

def get_processing_menu(is_premium: bool, has_operations: bool):
    """Get processing menu buttons"""
    buttons = []
    
    # Format conversion
    buttons.append([Button.inline("🔄 Convert Format", data="op_convert")])
    
    # Sample rate
    buttons.append([Button.inline("📊 Sample Rate", data="op_resample")])
    
    # Bitrate
    buttons.append([Button.inline("💿 Bitrate", data="op_bitrate")])
    
    if is_premium:
        # Effects (premium only)
        buttons.append([Button.inline("🎛️ Effects", data="op_effects")])
        buttons.append([Button.inline("✂️ Trim", data="op_trim")])
    
    # Normalize
    buttons.append([Button.inline("📈 Normalize", data="op_normalize")])
    
    # Actions
    if has_operations:
        buttons.append([
            Button.inline("✅ Process", data="action_process"),
            Button.inline("🗑️ Clear", data="action_clear")
        ])
    
    buttons.append([Button.inline("❌ Close", data="action_close")])
    
    return buttons

def get_format_menu(is_premium: bool):
    """Get format selection menu"""
    buttons = []
    
    # Free formats
    buttons.append([
        Button.inline("MP3", data="fmt_mp3"),
        Button.inline("AAC", data="fmt_aac"),
    ])
    buttons.append([
        Button.inline("OGG", data="fmt_ogg"),
        Button.inline("Opus", data="fmt_opus"),
    ])
    
    if is_premium:
        # Premium formats
        buttons.append([
            Button.inline("FLAC", data="fmt_flac"),
            Button.inline("WAV", data="fmt_wav"),
        ])
        buttons.append([
            Button.inline("AIFF", data="fmt_aiff"),
            Button.inline("ALAC", data="fmt_alac"),
        ])
    
    buttons.append([Button.inline("« Back", data="back_main")])
    
    return buttons

def get_sample_rate_menu(is_premium: bool):
    """Get sample rate selection menu"""
    buttons = []
    
    # Free sample rates
    buttons.append([
        Button.inline("22.05 kHz", data="sr_22050"),
        Button.inline("44.1 kHz", data="sr_44100"),
    ])
    
    if is_premium:
        # Premium sample rates
        buttons.append([
            Button.inline("48 kHz", data="sr_48000"),
            Button.inline("96 kHz", data="sr_96000"),
        ])
    
    buttons.append([Button.inline("« Back", data="back_main")])
    
    return buttons

def get_bitrate_menu(format_name: str = None, is_premium: bool = False):
    """Get bitrate selection menu, aware of selected/source format."""
    normalized = (format_name or "").lower()
    is_lossless_target = normalized in {"flac", "wav", "aiff", "alac"}

    if is_lossless_target and is_premium:
        options = LOSSLESS_BITRATE_OPTIONS
    else:
        options = LOSSY_BITRATE_OPTIONS

    buttons = []
    for row in _chunked(options, 2):
        buttons.append([Button.inline(f"{value} kbps", data=f"br_{value}") for value in row])

    buttons.append([Button.inline("✨ Original", data="br_original")])
    buttons.append([Button.inline("« Back", data="back_main")])
    return buttons

def get_effects_menu():
    """Get effects selection menu (premium only)"""
    buttons = [
        [Button.inline("🌊 Reverb", data="fx_reverb"), Button.inline("⏱️ Delay", data="fx_delay")],
        [Button.inline("🎸 Distortion", data="fx_distortion"), Button.inline("🎵 Chorus", data="fx_chorus")],
        [Button.inline("🔊 Bass Boost", data="fx_bass"), Button.inline("🎤 Vocal Enhance", data="fx_vocal")],
        [Button.inline("« Back", data="back_main")]
    ]
    return buttons

def get_bass_boost_menu():
    """Get bass boost frequency menu"""
    buttons = [
        [Button.inline("20 Hz", data="fx_bass_20"), Button.inline("40 Hz", data="fx_bass_40")],
        [Button.inline("60 Hz", data="fx_bass_60"), Button.inline("80 Hz", data="fx_bass_80")],
        [Button.inline("100 Hz", data="fx_bass_100"), Button.inline("120 Hz", data="fx_bass_120")],
        [Button.inline("« Back", data="op_effects")]
    ]
    return buttons

def get_vocal_enhance_menu():
    """Get vocal enhancement menu"""
    buttons = [
        [Button.inline("👨 Male Vocals", data="fx_vocal_male"), Button.inline("👩 Female Vocals", data="fx_vocal_female")],
        [Button.inline("« Back", data="op_effects")]
    ]
    return buttons

def get_effect_intensity_menu(effect_name: str, intensity: int):
    """Get effect intensity selection menu"""
    # intensity is 0-100
    
    # Calculate values
    minus_5 = max(0, intensity - 5)
    minus_1 = max(0, intensity - 1)
    plus_1 = min(100, intensity + 1)
    plus_5 = min(100, intensity + 5)
    
    buttons = [
        [
            Button.inline("-5%", data=f"fx_update_{effect_name}_{minus_5}"),
            Button.inline("-1%", data=f"fx_update_{effect_name}_{minus_1}"),
            Button.inline(f"{intensity}%", data="noop"),
            Button.inline("+1%", data=f"fx_update_{effect_name}_{plus_1}"),
            Button.inline("+5%", data=f"fx_update_{effect_name}_{plus_5}"),
        ],
        [
            Button.inline("✅ Done", data=f"fx_confirm_{effect_name}_{intensity}"),
            Button.inline("« Back", data="op_effects")
        ]
    ]
    return buttons

def get_help_menu(category: str = "main"):
    """Get help menu buttons"""
    if category == "main":
        buttons = [
            [Button.inline("📝 General", data="help_general"), Button.inline("🎛️ Effects", data="help_effects")],
            [Button.inline("💾 Formats", data="help_formats"), Button.inline("🌟 Premium", data="help_premium")],
            [Button.inline("❌ Close", data="action_close")]
        ]
        return "<b>📖 Help Menu</b>\nSelect a topic to learn more:", buttons
        
    elif category == "general":
        text = (
            "<b>📝 General Help</b>\n\n"
            "1. Send an audio file\n"
            "2. Select operations from the menu\n"
            "3. Click '✅ Process' to start\n"
            "4. Use '🗑️ Clear' to reset operations\n\n"
            "The bot supports parallel processing and maintains your session."
        )
        buttons = [[Button.inline("« Back", data="help_main")]]
        return text, buttons
        
    elif category == "effects":
        text = (
            "<b>🎛️ Effects Help</b>\n\n"
            "• <b>Reverb</b>: Add space and depth\n"
            "• <b>Delay</b>: Create echoes\n"
            "• <b>Bass Boost</b>: Enhance low frequencies\n"
            "• <b>Vocal Enhance</b>: Clarify vocals (Male/Female)\n"
            "• <b>Others</b>: Chorus, Distortion, Phaser\n\n"
            "<i>Select usage intensity for most effects!</i>"
        )
        buttons = [[Button.inline("« Back", data="help_main")]]
        return text, buttons
        
    elif category == "formats":
        text = (
            "<b>💾 Supported Formats</b>\n\n"
            "<b>Free:</b>\n"
            "• MP3, AAC, OGG, Opus\n\n"
            "<b>Premium:</b>\n"
            "• FLAC (Lossless)\n"
            "• WAV (Uncompressed)\n"
            "• AIFF, ALAC"
        )
        buttons = [[Button.inline("« Back", data="help_main")]]
        return text, buttons
        
    elif category == "premium":
        text = (
            "<b>🌟 Premium Benefits</b>\n\n"
            "• Access to Lossless formats\n"
            "• Advanced Effects\n"
            "• Higher sample rates (up to 96kHz)\n"
            "• Priority processing\n"
            "• No file size limits\n"
            "• Support development!"
        )
        buttons = [
            [Button.url("⭐ Buy Premium", "https://t.me/dotenv")],
            [Button.inline("« Back", data="help_main")]
        ]
        return text, buttons
    
    return "Unknown category", [[Button.inline("« Back", data="help_main")]]
