import unittest
from unittest.mock import MagicMock, patch
import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class TestGUISidebar(unittest.TestCase):
    def test_sidebar_creation(self):
        """
        Test that the GUI creates a favorites sidebar.
        """
        with patch('tkinter.Tk'), \
             patch('tkinter.ttk.Style'), \
             patch('tkinter.ttk.Frame') as mock_frame, \
             patch('tkinter.ttk.Label') as mock_label, \
             patch('tkinter.ttk.Entry'), \
             patch('tkinter.ttk.Checkbutton'), \
             patch('tkinter.ttk.Button'), \
             patch('tkinter.StringVar', side_effect=lambda value=None: MagicMock(get=MagicMock(return_value=value))), \
             patch('tkinter.IntVar', side_effect=lambda value=None: MagicMock(get=MagicMock(return_value=value))), \
             patch('tkinter.BooleanVar', side_effect=lambda value=None: MagicMock(get=MagicMock(return_value=value))):
            
            if 'gui_app' in sys.modules:
                del sys.modules['gui_app']
            from gui_app import HollandVacationApp
            
            app = HollandVacationApp()
            
            # Check for "Favorites" label
            label_texts = [call[1].get('text') for call in mock_label.call_args_list]
            self.assertTrue(any("Favorites" in str(t) for t in label_texts if t), "Missing Favorites label")

if __name__ == '__main__':
    unittest.main()

