
import unittest
from datetime import datetime
from models import Session, ProcessingOperation
from handlers.ui import get_help_menu

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

if __name__ == '__main__':
    unittest.main()
