import unittest
from unittest.mock import MagicMock, patch
import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class TestGUIScaffolding(unittest.TestCase):
    def test_gui_initialization(self):
        """
        Test that the GUI application initializes the main window correctly.
        """
        # We need to patch tkinter and ttk BEFORE importing gui_app
        with patch('tkinter.Tk') as mock_tk, \
             patch('tkinter.ttk.Style') as mock_style, \
             patch('tkinter.ttk.Frame') as mock_frame, \
             patch('tkinter.ttk.Label') as mock_label:
            
            # Re-import to apply patches if it was already imported
            if 'gui_app' in sys.modules:
                del sys.modules['gui_app']
            from gui_app import HollandVacationApp
            
            app = HollandVacationApp()
            
            # Verify title was set
            app.root.title.assert_called_with("Holland Vacation Deal Finder")
            
            # Verify background configuration (Dark Mode check)
            self.assertTrue(app.root.configure.called)
            
            # Verify style configuration
            mock_style.return_value.configure.assert_called()

if __name__ == '__main__':
    unittest.main()
