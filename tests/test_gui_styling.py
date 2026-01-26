import unittest
from unittest.mock import MagicMock, patch
import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class TestGUIStyling(unittest.TestCase):
    def test_styling_configuration(self):
        """
        Test that the GUI configures dark mode styles.
        """
        with patch('tkinter.Tk'), \
             patch('tkinter.ttk.Style') as mock_style, \
             patch('tkinter.ttk.Frame'), \
             patch('tkinter.ttk.Label'), \
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
            
            # Verify style.configure was called for different widget types
            # We expect at least Dark.TFrame and Dark.TLabel
            style_instance = mock_style.return_value
            configured_styles = [call[0][0] for call in style_instance.configure.call_args_list]
            
            self.assertIn("Dark.TFrame", configured_styles)
            self.assertIn("Dark.TLabel", configured_styles)
            self.assertIn("Dark.TButton", configured_styles)

if __name__ == '__main__':
    unittest.main()

