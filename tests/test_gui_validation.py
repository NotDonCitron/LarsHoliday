import unittest
from unittest.mock import MagicMock, patch
import sys
import os
from datetime import datetime, timedelta

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class TestGUIValidation(unittest.TestCase):
    def test_date_validation(self):
        """
        Test date validation logic.
        """
        # We need to mock everything to import gui_app without Tcl errors
        with patch('tkinter.Tk'), \
             patch('tkinter.ttk.Style'), \
             patch('tkinter.ttk.Frame'), \
             patch('tkinter.ttk.Label'), \
             patch('tkinter.ttk.Entry'), \
             patch('tkinter.ttk.Checkbutton'), \
             patch('tkinter.ttk.Button'), \
             patch('tkinter.StringVar', side_effect=lambda value=None: MagicMock(get=MagicMock(return_value=value))) as mock_string_var, \
             patch('tkinter.IntVar'), \
             patch('tkinter.BooleanVar'), \
             patch('tkinter.messagebox.showerror') as mock_showerror:
            
            if 'gui_app' in sys.modules:
                del sys.modules['gui_app']
            from gui_app import HollandVacationApp
            
            # Since we can't easily instantiate the full app due to complex setup in __init__,
            # we should refactor validation to be a static method or strictly isolated instance method.
            # But let's try to instantiate with full mocks.
            app = HollandVacationApp()
            
            # Test valid dates
            valid_checkin = "2026-02-15"
            valid_checkout = "2026-02-22"
            
            # Setup vars
            app.checkin_var.get.return_value = valid_checkin
            app.checkout_var.get.return_value = valid_checkout
            
            # Call validation (we expect this method to exist)
            result = app.validate_inputs()
            self.assertTrue(result, "Valid dates should pass")
            mock_showerror.assert_not_called()
            
            # Test invalid format
            app.checkin_var.get.return_value = "15-02-2026" # Wrong format
            result = app.validate_inputs()
            self.assertFalse(result, "Invalid format should fail")
            mock_showerror.assert_called()
            mock_showerror.reset_mock()
            
            # Test checkout before checkin
            app.checkin_var.get.return_value = "2026-02-22"
            app.checkout_var.get.return_value = "2026-02-15"
            result = app.validate_inputs()
            self.assertFalse(result, "Checkout before checkin should fail")
            mock_showerror.assert_called()

if __name__ == '__main__':
    unittest.main()
