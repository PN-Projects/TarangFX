
import unittest
import asyncio
from datetime import datetime
from models import Session, ProcessingOperation
from handlers.ui import get_help_menu, get_bitrate_menu
from processors import AsyncAudioProcessor
from pathlib import Path

class TestRefinements(unittest.TestCase):
    def test_multiple_effects(self):
        """Test that Session allows multiple effects of different types"""
        session = Session(user_id=123)
        
        # Add Reverb
        op1 = ProcessingOperation("effect", {"effect_type": "reverb", "intensity": 0.5}, priority=50)
        session.add_operation(op1)
        self.assertEqual(len(session.operations), 1)
        self.assertEqual(session.operations[0].parameters['effect_type'], 'reverb')
        
        # Add Bass Boost (should append)
        op2 = ProcessingOperation("effect", {"effect_type": "bass_boost", "frequency": 60}, priority=50)
        session.add_operation(op2)
        self.assertEqual(len(session.operations), 2)
        
        # Add Reverb again (should replace previous reverb)
        op3 = ProcessingOperation("effect", {"effect_type": "reverb", "intensity": 0.8}, priority=50)
        session.add_operation(op3)
        self.assertEqual(len(session.operations), 2)
        
        # Check values
        types = [op.parameters['effect_type'] for op in session.operations]
        self.assertIn('bass_boost', types)
        self.assertIn('reverb', types)
        
        # Verify intensity of reverb is updated
        reverb_op = next(op for op in session.operations if op.parameters['effect_type'] == 'reverb')
        self.assertEqual(reverb_op.parameters['intensity'], 0.8)

    def test_help_menu(self):
        """Test help menu generation"""
        # Main menu
        text, buttons = get_help_menu("main")
        self.assertIn("Help Menu", text)
        self.assertTrue(len(buttons) >= 3)
        
        # Sub menu
        text, buttons = get_help_menu("effects")
        self.assertIn("Bass Boost", text)
        self.assertEqual(buttons[0][0].data, b"help_main") # telethon buttons might store data as bytes or string depending on implementation, here assumes bytes for Telethon Button

    def test_bitrate_menu_lossy_defaults(self):
        """Lossy targets should keep the compact bitrate options."""
        buttons = get_bitrate_menu(format_name="mp3", is_premium=False)
        data_values = [btn.data.decode() for row in buttons for btn in row]

        self.assertIn("br_128", data_values)
        self.assertIn("br_320", data_values)
        self.assertNotIn("br_36000", data_values)
        self.assertIn("br_original", data_values)

    def test_bitrate_menu_flac_premium(self):
        """Premium FLAC targets should expose high bitrate presets up to 36000."""
        buttons = get_bitrate_menu(format_name="flac", is_premium=True)
        data_values = [btn.data.decode() for row in buttons for btn in row]

        self.assertIn("br_128", data_values)
        self.assertIn("br_320", data_values)
        self.assertIn("br_36000", data_values)
        self.assertIn("br_original", data_values)

    def test_flac_bitrate_maps_to_compression_level(self):
        """FLAC bitrate-style selections should map to a valid compression level."""
        processor = AsyncAudioProcessor(123, Path("input.flac"), [])

        self.assertEqual(processor._flac_compression_level(36000), 0)
        self.assertEqual(processor._flac_compression_level(128), 12)

    def test_bitrate_step_skips_when_convert_exists(self):
        """Bitrate operation should not double-transcode when convert will handle output."""
        operations = [
            ProcessingOperation("bitrate", {"bitrate": 320}, priority=90),
            ProcessingOperation("convert", {"format": "flac", "extension": ".flac", "bitrate": 320}, priority=100),
        ]
        processor = AsyncAudioProcessor(123, Path("input.mp3"), operations)

        # The bitrate adjustment should be treated as metadata-only in the presence of convert.
        result = asyncio.run(processor._adjust_bitrate({"bitrate": 320}))
        self.assertEqual(result, processor.current_file)

if __name__ == '__main__':
    unittest.main()
