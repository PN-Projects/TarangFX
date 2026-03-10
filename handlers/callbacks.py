"""Callback query handler for inline buttons"""
from loguru import logger
from core.cache import cache
from core.database import db
from models import Session, ProcessingOperation, OPERATION_PRIORITIES
from handlers.ui import get_processing_menu, get_format_menu, get_sample_rate_menu, get_bitrate_menu, get_effects_menu, get_effect_intensity_menu, get_bass_boost_menu, get_vocal_enhance_menu, get_help_menu, get_status_text
from processors import AsyncAudioProcessor
from pathlib import Path

async def handle_callback(event, bot, concurrency):
    """Handle inline button callbacks - ASYNC"""
    user_id = event.sender_id
    data = event.data.decode('utf-8')
    
    try:
        # Handle help menu (no session required)
        if data.startswith("help_"):
            await handle_help(event, data)
            return

        # Get session
        session_data = await cache.get_session(user_id)
        if not session_data:
            await event.answer("Session expired. Please send a new file.", alert=True)
            return
        
        session = Session.from_dict(session_data)
        session.message_id = event.message_id
        
        # Get user premium status
        is_premium = await db.is_premium(user_id)
        
        # Handle different callbacks
        if data.startswith("op_"):
            await handle_operation_select(event, session, data, is_premium)
        elif data.startswith("fmt_") or data.startswith("sr_") or data.startswith("br_") or data.startswith("fx_") and not data.startswith("fx_update_") and not data.startswith("fx_confirm_"):
            await handle_parameter_select(event, session, data)
        elif data.startswith("fx_update_"):
             await handle_effect_update(event, data)
        elif data.startswith("fx_confirm_"):
             await handle_effect_confirm(event, session, data, is_premium)
        elif data.startswith("action_"):
            await handle_action(event, session, data, bot, concurrency)
        elif data.startswith("back_"):
            await handle_back(event, session, is_premium)
        else:
            await event.answer("Unknown action")
        
    except Exception as e:
        logger.error(f"Error in callback handler: {e}")
        await event.answer("❌ An error occurred", alert=True)

async def handle_operation_select(event, session, data, is_premium):
    """Handle operation type selection"""
    op_type = data.replace("op_", "")
    
    if op_type == "convert":
        await event.edit(buttons=get_format_menu(is_premium))
    elif op_type == "resample":
        await event.edit(buttons=get_sample_rate_menu(is_premium))
    elif op_type == "bitrate":
        await event.edit(buttons=get_bitrate_menu())
    elif op_type == "effects":
        if not is_premium:
            await event.answer("Premium feature!", alert=True)
            return
        await event.edit(buttons=get_effects_menu())
    elif op_type == "normalize":
        # Add normalize operation
        operation = ProcessingOperation(
            operation_type="normalize",
            parameters={},
            priority=OPERATION_PRIORITIES.get("normalize", 80)
        )
        session.add_operation(operation)
        await cache.save_session(session.user_id, session.to_dict())
        await event.answer("✅ Normalize added")
        await event.edit(text=get_status_text(session, is_premium), buttons=get_processing_menu(is_premium, bool(session.operations)), parse_mode='html')
    elif op_type == "trim":
        if not is_premium:
            await event.answer("Premium feature!", alert=True)
            return
        await event.answer("Trim not implemented in demo", alert=True)

async def handle_parameter_select(event, session, data):
    """Handle parameter selection"""
    is_premium = await db.is_premium(session.user_id)
    
    if data.startswith("fmt_"):
        format_name = data.replace("fmt_", "")
        operation = ProcessingOperation(
            operation_type="convert",
            parameters={"format": format_name, "extension": f".{format_name}"},
            priority=OPERATION_PRIORITIES.get("convert", 100)
        )
        session.add_operation(operation)
        await cache.save_session(session.user_id, session.to_dict())
        await event.answer(f"✅ Convert to {format_name.upper()}")
        await event.edit(text=get_status_text(session, is_premium), buttons=get_processing_menu(is_premium, True), parse_mode='html')
        
    elif data.startswith("sr_"):
        sample_rate = int(data.replace("sr_", ""))
        operation = ProcessingOperation(
            operation_type="resample",
            parameters={"sample_rate": sample_rate},
            priority=OPERATION_PRIORITIES.get("resample", 20)
        )
        session.add_operation(operation)
        await cache.save_session(session.user_id, session.to_dict())
        await event.answer(f"✅ Sample rate: {sample_rate} Hz")
        await event.edit(text=get_status_text(session, is_premium), buttons=get_processing_menu(is_premium, True), parse_mode='html')
        
    elif data.startswith("br_"):
        bitrate_str = data.replace("br_", "")
        
        if bitrate_str == "original":
            # No bitrate operation needed (or a dummy one to confirm selection)
            # Actually, better to just NOT add a bitrate op, effectively keeping original
            # BUT we want to show it in status. So let's add an op with special param.
            operation = ProcessingOperation(
                operation_type="bitrate",
                parameters={"bitrate": "original"},
                priority=OPERATION_PRIORITIES.get("bitrate", 90)
            )
            await event.answer("✅ Keeping original bitrate")
        else:
            bitrate = int(bitrate_str)
            operation = ProcessingOperation(
                operation_type="bitrate",
                parameters={"bitrate": bitrate},
                priority=OPERATION_PRIORITIES.get("bitrate", 90)
            )
            await event.answer(f"✅ Bitrate: {bitrate} kbps")
            
        session.add_operation(operation)
        await cache.save_session(session.user_id, session.to_dict())
        await event.edit(text=get_status_text(session, is_premium), buttons=get_processing_menu(is_premium, True), parse_mode='html')
        
    elif data.startswith("fx_"):
        effect = data.replace("fx_", "")
        
        if effect == "bass":
             await event.edit(text="🔊 Select Bass Frequency to Boost:", buttons=get_bass_boost_menu(), parse_mode='html')
        elif effect == "vocal":
             await event.edit(text="🎤 Select Vocal Type:", buttons=get_vocal_enhance_menu(), parse_mode='html')
        elif effect.startswith("bass_"):
            # fx_bass_{freq}
            freq = int(effect.replace("bass_", ""))
            operation = ProcessingOperation(
                operation_type="effect",
                parameters={"effect_type": "bass_boost", "frequency": freq, "gain_db": 3}, # Fixed 3dB gain per task
                priority=OPERATION_PRIORITIES.get("effects", 50)
            )
            session.add_operation(operation)
            await cache.save_session(session.user_id, session.to_dict())
            await event.answer(f"✅ Bass Boost: {freq} Hz")
            await event.edit(text=get_status_text(session, is_premium), buttons=get_processing_menu(is_premium, True), parse_mode='html')
            
        elif effect.startswith("vocal_"):
            # fx_vocal_{type}
            vocal_type = effect.replace("vocal_", "")
            operation = ProcessingOperation(
                operation_type="effect",
                parameters={"effect_type": "vocal_enhance", "vocal_type": vocal_type},
                priority=OPERATION_PRIORITIES.get("effects", 50)
            )
            session.add_operation(operation)
            await cache.save_session(session.user_id, session.to_dict())
            await event.answer(f"✅ Vocal Enhance: {vocal_type.title()}")
            await event.edit(text=get_status_text(session, is_premium), buttons=get_processing_menu(is_premium, True), parse_mode='html')

        else:
            # Show intensity menu for standard effects
            await event.edit(
                text=f"🎛️ Adjust <b>{effect.title()}</b> Intensity:",
                buttons=get_effect_intensity_menu(effect, 50), # Default 50%
                parse_mode='html'
            )

async def handle_effect_update(event, data):
    """Handle effect intensity update"""
    # format: fx_update_{effect}_{intensity}
    parts = data.split("_")
    effect = parts[2]
    intensity = int(parts[3])
    
    await event.edit(
        text=f"🎛️ Adjust <b>{effect.title()}</b> Intensity:",
        buttons=get_effect_intensity_menu(effect, intensity),
        parse_mode='html'
    )

async def handle_effect_confirm(event, session, data, is_premium):
    """Handle effect intensity confirmation"""
    # format: fx_confirm_{effect}_{intensity}
    parts = data.split("_")
    effect = parts[2]
    intensity = int(parts[3])
    
    # Normalize intensity to 0.0 - 1.0 for processing
    intensity_float = intensity / 100.0
    
    operation = ProcessingOperation(
        operation_type="effect",
        parameters={"effect_type": effect, "intensity": intensity_float},
        priority=OPERATION_PRIORITIES.get("effects", 50)
    )
    session.add_operation(operation)
    await cache.save_session(session.user_id, session.to_dict())
    
    await event.answer(f"✅ Effect: {effect} ({intensity}%)")
    await event.edit(text=get_status_text(session, is_premium), buttons=get_processing_menu(is_premium, True), parse_mode='html')

async def handle_action(event, session, data, bot, concurrency):
    """Handle action buttons"""
    action = data.replace("action_", "")
    is_premium = await db.is_premium(session.user_id)
    
    if action == "process":
        if not session.operations:
            await event.answer("No operations selected!", alert=True)
            return
        
        await event.edit("⚙️ Processing... This may take a while.")
        
        try:
            # Get sorted operations
            operations = session.get_sorted_operations()
            input_file = Path(session.audio_file['file_path'])
            
            # Process with semaphore
            async with concurrency.processing_semaphore:
                processor = AsyncAudioProcessor(session.user_id, input_file, operations)
                output_file = await processor.process()
                await processor.cleanup()
            
            # Send processed file
            await bot.send_file(
                session.user_id,
                output_file,
                caption="✅ Processing complete!",
                force_document=False
            )
            
            # Cleanup
            await concurrency.cleanup_user_files(session.user_id)
            await cache.delete_session(session.user_id)
            await event.delete()
            
        except Exception as e:
            logger.error(f"Processing error: {e}")
            await event.edit(f"❌ Processing failed: {str(e)[:100]}")
            
    elif action == "clear":
        session.operations.clear()
        await cache.save_session(session.user_id, session.__dict__)
        await event.answer("🗑️ Operations cleared")
        await event.edit(text=get_status_text(session, is_premium), buttons=get_processing_menu(is_premium, False), parse_mode='html')
        
    elif action == "close":
        await concurrency.cleanup_user_files(session.user_id)
        await cache.delete_session(session.user_id)
        await event.delete()

async def handle_back(event, session, is_premium):
    """Handle back button"""
    await event.edit(text=get_status_text(session, is_premium), buttons=get_processing_menu(is_premium, bool(session.operations)), parse_mode='html')

async def handle_help(event, data):
    """Handle help menu navigation"""
    # format: help_{category}
    category = data.replace("help_", "")
    text, buttons = get_help_menu(category)
    await event.edit(text=text, buttons=buttons, parse_mode='html')
