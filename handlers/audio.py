"""
Async Audio File Handler - NO BLOCKING OPERATIONS
Async Audio File Handler - NO BLOCKING OPERATIONS
Downloads files asynchronously with semaphore limits
"""
from telethon import Button

import asyncio
import hashlib
from pathlib import Path
from datetime import datetime
from loguru import logger
import mutagen

from config import config
from core.database import db
from core.cache import cache


async def handle_audio_file(event, bot, concurrency):
    """Handle audio file upload - FULLY ASYNC"""
    user_id = event.sender_id
    
    try:
        # Check concurrency
        if not await concurrency.can_user_process(user_id):
            await event.respond(
                "⏳ You already have the maximum number of operations running.\n"
                "Please wait for them to complete."
            )
            return
        
        # Step 2: Rate limiting check (async, cached in Redis)
        is_premium = await db.is_premium(user_id)  # Cached
        
        if is_premium:
            max_rpm = config.PREMIUM_REQUESTS_PER_MINUTE
        else:
            max_rpm = config.FREE_REQUESTS_PER_MINUTE
        
        allowed = await cache.check_rate_limit(user_id, max_rpm, 60)
        
        if not allowed:
            reset_time = await cache.get_rate_limit_reset(user_id)
            await event.respond(
                f"⏸️ Rate limit exceeded.\n"
                f"Please wait {reset_time} seconds before sending more files."
            )
            return
        
        # Step 3: Get file info
        if event.message.audio:
            file = event.message.audio
            # Find filename attribute
            file_name = "audio.mp3"
            if file.attributes:
                for attr in file.attributes:
                    if hasattr(attr, 'file_name'):
                        file_name = attr.file_name
                        break
            file_size = file.size
        elif event.message.document:
            file = event.message.document
            file_name = "audio.mp3"
            if file.attributes:
                for attr in file.attributes:
                    if hasattr(attr, 'file_name'):
                        file_name = attr.file_name
                        break
            file_size = file.size
        else:
            return
        
        # Step 4: Validate file size (instant)
        if file_size > config.max_file_size_bytes:
            await event.respond(
                f"❌ File too large!\n"
                f"Maximum: {config.MAX_FILE_SIZE_MB} MB\n"
                f"Your file: {file_size / (1024**2):.1f} MB"
            )
            return
        
        # Step 5: Send status message (async)
        status_msg = await event.respond(
            "⏳ Downloading your audio file...\n"
            f"<code>{file_name}</code>\n"
            f"Size: {file_size / (1024**2):.1f} MB",
            parse_mode='html'
        )
        
        # Step 6: Generate operation ID
        operation_id = hashlib.md5(
            f"{user_id}{datetime.utcnow().timestamp()}".encode()
        ).hexdigest()
        
        # Register operation
        await concurrency.register_operation(user_id, operation_id)
        
        try:
            # Download file
            file_path = await download_file_async(
                event.message,
                user_id,
                file_name,
                concurrency
            )
            
            # Step 8: Update status
            await status_msg.edit(
                "🔍 Analyzing audio format...\n"
                f"<code>{file_name}</code>",
                parse_mode='html'
            )
            
            # Step 9: Detect format ASYNCHRONOUSLY (uses executor for CPU-bound work)
            audio_info = await detect_format_async(file_path)
            
            if not audio_info:
                await status_msg.edit(
                    "❌ Could not detect audio format.\n"
                    "Please ensure it's a valid audio file."
                )
                await concurrency.cleanup_user_files(user_id)
                return
            
            # Step 10: Check duration limit for free users
            duration = audio_info.get('duration', 0)
            
            if not is_premium and duration > config.free_max_duration_seconds:
                await status_msg.edit(
                    f"❌ File too long for free users!\n"
                    f"Maximum: {config.FREE_TIER_MAX_DURATION_MIN} minutes\n"
                    f"Your file: {duration / 60:.1f} minutes\n\n"
                    f"💎 Upgrade to Premium for unlimited duration!\n"
                    f"Contact @{config.SUPPORT_USERNAME}"
                )
                await concurrency.cleanup_user_files(user_id)
                return
            
            # Step 10b: Check format restriction (Lossless is Premium only)
            format_name = audio_info.get('format', '').lower()
            lossless_formats = ['flac', 'wav', 'aiff', 'alac', 'pcm_s16le', 'pcm_s24le']
            
            # Simple check based on format name or detected codec
            is_lossless = any(fmt in format_name for fmt in lossless_formats)
            
            if not is_premium and is_lossless:
                await status_msg.edit(
                    f"💎 <b>Premium Feature!</b>\n\n"
                    f"Processing <b>Lossless Audio</b> ({format_name.upper()}) is a Premium feature.\n"
                    f"Free users can process MP3, AAC, OGG, and Opus.\n\n"
                    f"Upgrade to Premium for studio-quality processing!",
                    buttons=[[Button.url("⭐ Buy Premium", "https://t.me/dotenv")]],
                    parse_mode='html'
                )
                await concurrency.cleanup_user_files(user_id)
                return

            # Step 11: Save session to cache (async)
            session_data = {
                "user_id": user_id,
                "audio_file": {
                    "file_path": str(file_path),
                    "file_name": file_name,
                    "file_size": file_size,
                    "duration": duration,
                    "format": audio_info.get("format"),
                    "sample_rate": audio_info.get("sample_rate"),
                    "bit_rate": audio_info.get("bitrate"),
                    "channels": audio_info.get("channels"),
                },
                "operations": [],
                "created_at": datetime.utcnow().isoformat(),
            }
            
            await cache.save_session(user_id, session_data)
            
            # Step 12: Send UI (async)
            from handlers.ui import get_processing_menu
            
            await status_msg.edit(
                f"✅ <b>Audio File Ready!</b>\n\n"
                f"📄 <code>{file_name}</code>\n"
                f"⏱️ Duration: {duration:.1f}s\n"
                f"💾 Size: {file_size / (1024**2):.1f} MB\n"
                f"🎵 Format: {audio_info.get('format', 'Unknown')}\n\n"
                f"Select operations below, then press <b>✅ Process</b>",
                buttons=get_processing_menu(is_premium, has_operations=False),
                parse_mode='html'
            )
            
            logger.info(
                f"[ASYNC] User {user_id} uploaded {file_name} "
                f"({duration:.1f}s, {file_size / (1024**2):.1f}MB) - NO BLOCKING!"
            )
            
        finally:
            # Unregister operation
            await concurrency.unregister_operation(user_id, operation_id)
            
    except asyncio.CancelledError:
        logger.info(f"File download cancelled for user {user_id}")
        raise
    except Exception as e:
        logger.error(f"Error handling audio file for user {user_id}: {e}")
        try:
            await event.respond(f"❌ Error: {str(e)[:100]}")
        except:
            pass


async def download_file_async(message, user_id: int, file_name: str, concurrency) -> Path:
    """
    Download file ASYNCHRONOUSLY with semaphore limits
    
    This is the KEY function - it prevents blocking!
    
    Uses:
    - User semaphore (prevent one user from hogging)
    - Global download semaphore (prevent system overload)
    - Async download (non-blocking I/O)
    """
    # Create user directory
    user_dir = config.TEMP_DIR / str(user_id)
    user_dir.mkdir(parents=True, exist_ok=True)
    
    # Sanitize filename
    safe_name = sanitize_filename(file_name)
    file_path = user_dir / f"input_{safe_name}"
    
    # Get user semaphore
    user_sem = await concurrency.get_user_semaphore(user_id)
    
    # Download with double semaphore protection
    async with user_sem:  # Per-user limit
        async with concurrency.download_semaphore:  # Global limit
            logger.info(f"[ASYNC] Starting download for user {user_id}: {file_name}")
            
            # Use download_file for PARALLEL downloads (much faster)
            # aiofiles (iter_download) is sequential and slow for large files
            # Writing 512KB to disk is negligible blocking, network is the bottleneck
            
            async def _progress(current, total):
                if total and current % (1024*1024) == 0: # Log every 1MB
                    logger.info(f"[ASYNC] Downloading {user_id}: {current/1024/1024:.1f}/{total/1024/1024:.1f} MB")

            await message.client.download_file(
                message.media,
                str(file_path),
                progress_callback=_progress,
                part_size_kb=512
            )
            
            # Track file for cleanup
            await concurrency.track_file(file_path)
            
            logger.info(f"[ASYNC] Download complete for user {user_id}: {file_path}")
            
            return file_path


async def detect_format_async(file_path: Path) -> dict:
    """
    Detect audio format ASYNCHRONOUSLY using executor
    
    Uses executor because mutagen is CPU-bound (blocking)
    This keeps event loop free!
    """
    loop = asyncio.get_event_loop()
    
    try:
        # Run in executor to avoid blocking
        audio_info = await loop.run_in_executor(
            None,  # Use default executor
            _detect_format_sync,
            file_path
        )
        return audio_info
        
    except Exception as e:
        logger.error(f"Format detection failed for {file_path}: {e}")
        
        # Fallback: try FFprobe
        return await detect_format_ffprobe(file_path)


def _detect_format_sync(file_path: Path) -> dict:
    """
    Synchronous format detection using mutagen
    Runs in executor, not in main event loop
    """
    try:
        audio = mutagen.File(str(file_path), easy=True)
        
        if audio is None:
            raise ValueError("Could not detect format")
        
        return {
            'duration': audio.info.length if hasattr(audio.info, 'length') else 0,
            'sample_rate': getattr(audio.info, 'sample_rate', None),
            'bitrate': getattr(audio.info, 'bitrate', 0) // 1000 if hasattr(audio.info, 'bitrate') else None,
            'channels': getattr(audio.info, 'channels', None),
            'format': type(audio).__name__,
        }
        
    except Exception as e:
        logger.warning(f"Mutagen failed: {e}")
        raise


async def detect_format_ffprobe(file_path: Path) -> dict:
    """
    Fallback format detection using FFprobe - ASYNC
    """
    try:
        cmd = [
            'ffprobe',
            '-v', 'quiet',
            '-print_format', 'json',
            '-show_format',
            '-show_streams',
            str(file_path)
        ]
        
        # Run ffprobe asynchronously
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await proc.communicate()
        
        if proc.returncode == 0:
            import json
            data = json.loads(stdout)
            
            format_info = data.get('format', {})
            streams = data.get('streams', [])
            audio_stream = next((s for s in streams if s.get('codec_type') == 'audio'), {})
            
            return {
                'duration': float(format_info.get('duration', 0)),
                'sample_rate': int(audio_stream.get('sample_rate', 0)) if audio_stream.get('sample_rate') else None,
                'bitrate': int(format_info.get('bit_rate', 0)) // 1000 if format_info.get('bit_rate') else None,
                'channels': int(audio_stream.get('channels', 0)) if audio_stream.get('channels') else None,
                'format': format_info.get('format_name', 'unknown'),
            }
        else:
            raise ValueError(f"ffprobe failed: {stderr.decode()}")
            
    except Exception as e:
        logger.error(f"FFprobe fallback failed: {e}")
        return {}


def sanitize_filename(filename: str) -> str:
    """Sanitize filename to prevent path traversal"""
    import os
    filename = os.path.basename(filename)
    dangerous_chars = ['..', '/', '\\', '\0']
    for char in dangerous_chars:
        filename = filename.replace(char, '_')
    
    if not filename or filename.startswith('.'):
        filename = f"audio_{hashlib.md5(filename.encode()).hexdigest()[:8]}"
    
    return filename
