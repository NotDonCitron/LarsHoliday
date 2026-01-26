import unittest
from unittest.mock import MagicMock, patch
import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class TestGUIInputs(unittest.TestCase):
    def test_input_creation(self):
        """
        Test that the GUI creates all required input fields.
        """
        with patch('tkinter.Tk') as mock_tk, \
             patch('tkinter.ttk.Style'), \
             patch('tkinter.ttk.Frame'), \
             patch('tkinter.ttk.Label') as mock_label, \
             patch('tkinter.ttk.Entry') as mock_entry, \
             patch('tkinter.ttk.Checkbutton') as mock_checkbutton, \
             patch('tkinter.ttk.Button') as mock_button, \
             patch('tkinter.StringVar') as mock_string_var, \
             patch('tkinter.IntVar') as mock_int_var, \
             patch('tkinter.BooleanVar') as mock_bool_var:
            
            # Re-import
            if 'gui_app' in sys.modules:
                del sys.modules['gui_app']
            from gui_app import HollandVacationApp
            
            app = HollandVacationApp()
            
            # We expect Label creation for:
            # Cities, Check-in, Check-out, Adults, Budget, Pets
            expected_labels = ["Cities (comma-separated):", "Check-in (YYYY-MM-DD):", "Check-out (YYYY-MM-DD):", "Number of Adults:", "Max Budget (€/night):"]
            
            # Get all text arguments passed to Label constructor
            created_labels = []
            for call in mock_label.call_args_list:
                kwargs = call[1]
                if 'text' in kwargs:
                    created_labels.append(kwargs['text'])
            
            for label in expected_labels:
                self.assertIn(label, created_labels, f"Missing label: {label}")
                
            # Verify Checkbutton for dogs
            mock_checkbutton.assert_called()
            # Check if text "Allow Dogs" was passed
            checkbutton_texts = [call[1].get('text') for call in mock_checkbutton.call_args_list]
            self.assertIn("🐕 Allow Dogs (Hundefreundlich)", checkbutton_texts)
            
            # Verify Search Button
            mock_button.assert_called()
            button_texts = [call[1].get('text') for call in mock_button.call_args_list]
            self.assertIn("🔍 Search Best Deals", button_texts)

if __name__ == '__main__':
    unittest.main()
