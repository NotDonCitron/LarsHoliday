import tkinter as tk
from tkinter import ttk

class HollandVacationApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Holland Vacation Deal Finder")
        self.root.geometry("800x600")
        
        # Dark Theme Configuration
        self.bg_color = "#2E2E2E"
        self.fg_color = "#FFFFFF"
        self.root.configure(bg=self.bg_color)
        
        # Configure styles
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("Dark.TFrame", background=self.bg_color)
        style.configure("Dark.TLabel", background=self.bg_color, foreground=self.fg_color)
        style.configure("Dark.TButton", background="#4A4A4A", foreground=self.fg_color)
        
        self.setup_ui()

    def setup_ui(self):
        # Main Layout
        self.main_frame = ttk.Frame(self.root, style="Dark.TFrame")
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Title
        title_label = ttk.Label(
            self.main_frame, 
            text="Holland Vacation Deal Finder", 
            style="Dark.TLabel",
            font=("Helvetica", 16, "bold")
        )
        title_label.pack(pady=(0, 20))

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    app = HollandVacationApp()
    app.run()
