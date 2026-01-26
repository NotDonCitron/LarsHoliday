import unittest
from unittest.mock import MagicMock, patch
import sys
import os
import threading

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class TestGUIIntegration(unittest.TestCase):
    def test_search_integration(self):
        """
        Test that the GUI integrates with the agent and runs search in a thread.
        """
        # Mock ALL the things
        with patch('tkinter.Tk'), \
             patch('tkinter.ttk.Style'), \
             patch('tkinter.ttk.Frame'), \
             patch('tkinter.ttk.Label'), \
             patch('tkinter.ttk.Entry'), \
             patch('tkinter.ttk.Checkbutton'), \
             patch('tkinter.ttk.Button'), \
             patch('tkinter.StringVar', side_effect=lambda value=None: MagicMock(get=MagicMock(return_value=value))) as mock_string_var, \
             patch('tkinter.IntVar', side_effect=lambda value=None: MagicMock(get=MagicMock(return_value=value))) as mock_int_var, \
             patch('tkinter.BooleanVar', side_effect=lambda value=None: MagicMock(get=MagicMock(return_value=value))), \
             patch('tkinter.messagebox.showerror'), \
             patch('threading.Thread') as mock_thread, \
             patch('holland_agent.HollandVacationAgent') as mock_agent_class:
            
            if 'gui_app' in sys.modules:
                del sys.modules['gui_app']
            from gui_app import HollandVacationApp
            
            app = HollandVacationApp()
            
            # Setup valid inputs so validation passes
            app.cities_var.get.return_value = "Amsterdam"
            app.checkin_var.get.return_value = "2026-02-15"
            app.checkout_var.get.return_value = "2026-02-22"
            app.adults_var.get.return_value = 2
            app.budget_var.get.return_value = 200
            app.allow_dogs_var.get.return_value = True
            
            # Verify agent initialization
            mock_agent_class.assert_called()
            
            # Call start_search
            app.start_search()
            
            # Verify it created a thread
            mock_thread.assert_called()
            
            # Verify the thread target is the wrapper method
            args, kwargs = mock_thread.call_args
            target = kwargs.get('target')
            thread_args = kwargs.get('args')
            self.assertTrue(target, "Thread should have a target")
            
            # Simulate the thread running the target
            # We assume the target is app.run_search_thread or similar
            # And it should call agent.find_best_deals
            
            # Let's inspect what 'target' is
            # It should be a bound method
            self.assertTrue(callable(target))
            
            # Execute the target function to verify it calls the agent
            # We need to mock asyncio.run inside it probably?
            # Or assume agent.find_best_deals is async and we use asyncio.run
            
            with patch('asyncio.run') as mock_asyncio_run:
                target(*thread_args)
                
                # Check if agent search was called
                # agent instance is mock_agent_class.return_value
                agent_instance = mock_agent_class.return_value
                
                # We expect asyncio.run to be called with a coroutine
                mock_asyncio_run.assert_called()
                
                # Can't easily check exactly what coroutine was passed to run without more complex mocking,
                # but we can verify that finding deals is part of the flow.

if __name__ == '__main__':
    unittest.main()
