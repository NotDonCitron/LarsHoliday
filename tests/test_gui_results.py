import unittest
from unittest.mock import MagicMock, patch
import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class TestGUIResults(unittest.TestCase):
    def test_search_completion(self):
        """
        Test that the GUI handles search completion (updates UI, shows button).
        """
        with patch('tkinter.Tk') as mock_tk, \
             patch('tkinter.ttk.Style'), \
             patch('tkinter.ttk.Frame'), \
             patch('tkinter.ttk.Label') as mock_label, \
             patch('tkinter.ttk.Entry'), \
             patch('tkinter.ttk.Checkbutton'), \
             patch('tkinter.ttk.Button') as mock_button, \
             patch('tkinter.StringVar', side_effect=lambda value=None: MagicMock(get=MagicMock(return_value=value))), \
             patch('tkinter.IntVar', side_effect=lambda value=None: MagicMock(get=MagicMock(return_value=value))), \
             patch('tkinter.BooleanVar', side_effect=lambda value=None: MagicMock(get=MagicMock(return_value=value))), \
             patch('webbrowser.open') as mock_webbrowser_open:
            
            if 'gui_app' in sys.modules:
                del sys.modules['gui_app']
            from gui_app import HollandVacationApp
            
            app = HollandVacationApp()
            
            # Setup successful results
            mock_results = {"top_10_deals": [{"name": "Deal 1"}], "total_deals_found": 1}
            
            # Simulate calling search_complete (which should be called from the thread)
            # We expect this method to exist and update the UI
            try:
                app.search_complete(mock_results)
            except AttributeError:
                self.fail("HollandVacationApp has no attribute 'search_complete'")
            
            # Verify status label update
            # status_label is created in setup_ui. It's a Mock.
            app.status_label.config.assert_called()
            # Check text
            call_args = app.status_label.config.call_args
            self.assertIn("Search complete", call_args[1].get('text', ''))
            
            # Verify "Open Report" button creation or enabling
            # We check if a button with text "Open Report" was created
            button_texts = [call[1].get('text') for call in mock_button.call_args_list]
            self.assertIn("📄 Open HTML Report", button_texts)
            
            # Simulate clicking "Open Report"
            app.open_report()
            mock_webbrowser_open.assert_called()

if __name__ == '__main__':
    unittest.main()
