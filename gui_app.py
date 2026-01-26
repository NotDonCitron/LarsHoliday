import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
import threading
import asyncio
import webbrowser
import os
from holland_agent import HollandVacationAgent

class HollandVacationApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Holland Vacation Deal Finder")
        self.root.geometry("800x600")
        
        # Dark Theme Configuration
        self.bg_color = "#2E2E2E"
        self.fg_color = "#FFFFFF"
        self.root.configure(bg=self.bg_color)
        
        # Initialize Agent
        self.agent = HollandVacationAgent()
        
        # Configure styles
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("Dark.TFrame", background=self.bg_color)
        style.configure("Dark.TLabel", background=self.bg_color, foreground=self.fg_color)
        style.configure("Dark.TButton", background="#4A4A4A", foreground=self.fg_color)
        style.configure("Dark.TCheckbutton", background=self.bg_color, foreground=self.fg_color)
        
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
        
        self.create_input_form()
        
        # Status Area
        self.status_label = ttk.Label(self.main_frame, text="", style="Dark.TLabel")
        self.status_label.pack(pady=10)
        
        # Results Area (Open Report Button) - Hidden initially
        self.open_report_btn = ttk.Button(
            self.main_frame,
            text="Open Report",
            style="Dark.TButton",
            command=self.open_report
        )
        # We don't pack it yet

    def create_input_form(self):
        # Form Container
        form_frame = ttk.Frame(self.main_frame, style="Dark.TFrame")
        form_frame.pack(fill=tk.X, pady=10)
        
        # Grid Configuration
        form_frame.columnconfigure(1, weight=1)
        
        # --- Cities ---
        ttk.Label(form_frame, text="Cities:", style="Dark.TLabel").grid(row=0, column=0, sticky="w", pady=5)
        self.cities_var = tk.StringVar(value="Amsterdam, Rotterdam, Zandvoort")
        self.cities_entry = ttk.Entry(form_frame, textvariable=self.cities_var)
        self.cities_entry.grid(row=0, column=1, sticky="ew", padx=(10, 0))
        
        # --- Dates ---
        # Check-in
        ttk.Label(form_frame, text="Check-in (YYYY-MM-DD):", style="Dark.TLabel").grid(row=1, column=0, sticky="w", pady=5)
        self.checkin_var = tk.StringVar(value="2026-02-15")
        self.checkin_entry = ttk.Entry(form_frame, textvariable=self.checkin_var)
        self.checkin_entry.grid(row=1, column=1, sticky="ew", padx=(10, 0))
        
        # Check-out
        ttk.Label(form_frame, text="Check-out (YYYY-MM-DD):", style="Dark.TLabel").grid(row=2, column=0, sticky="w", pady=5)
        self.checkout_var = tk.StringVar(value="2026-02-22")
        self.checkout_entry = ttk.Entry(form_frame, textvariable=self.checkout_var)
        self.checkout_entry.grid(row=2, column=1, sticky="ew", padx=(10, 0))
        
        # --- Group & Budget ---
        # Adults
        ttk.Label(form_frame, text="Adults:", style="Dark.TLabel").grid(row=3, column=0, sticky="w", pady=5)
        self.adults_var = tk.IntVar(value=4)
        self.adults_entry = ttk.Entry(form_frame, textvariable=self.adults_var)
        self.adults_entry.grid(row=3, column=1, sticky="ew", padx=(10, 0))
        
        # Budget
        ttk.Label(form_frame, text="Max Budget (€):", style="Dark.TLabel").grid(row=4, column=0, sticky="w", pady=5)
        self.budget_var = tk.IntVar(value=250)
        self.budget_entry = ttk.Entry(form_frame, textvariable=self.budget_var)
        self.budget_entry.grid(row=4, column=1, sticky="ew", padx=(10, 0))
        
        # --- Pet Toggle ---
        self.allow_dogs_var = tk.BooleanVar(value=True)
        self.dogs_check = ttk.Checkbutton(
            form_frame, 
            text="Allow Dogs", 
            variable=self.allow_dogs_var,
            style="Dark.TCheckbutton"
        )
        self.dogs_check.grid(row=5, column=0, columnspan=2, sticky="w", pady=15)
        
        # --- Search Button ---
        self.search_btn = ttk.Button(
            self.main_frame,
            text="Search Deals",
            style="Dark.TButton",
            command=self.start_search
        )
        self.search_btn.pack(pady=20, fill=tk.X)

    def validate_inputs(self) -> bool:
        """Validate form inputs"""
        checkin = self.checkin_var.get()
        checkout = self.checkout_var.get()
        
        try:
            d1 = datetime.strptime(checkin, "%Y-%m-%d")
            d2 = datetime.strptime(checkout, "%Y-%m-%d")
            
            if d2 <= d1:
                messagebox.showerror("Invalid Dates", "Check-out date must be after check-in date.")
                return False
                
            if d1 < datetime.now():
                pass
                
        except ValueError:
            messagebox.showerror("Invalid Date Format", "Please use YYYY-MM-DD format.")
            return False
            
        return True

    def start_search(self):
        if not self.validate_inputs():
            return
        
        self.status_label.config(text="Starting search... Please wait.")
        self.search_btn.state(['disabled'])
        self.open_report_btn.pack_forget() # Hide previous button if any
        
        # Capture values to pass to thread
        cities = [c.strip() for c in self.cities_var.get().split(",")]
        checkin = self.checkin_var.get()
        checkout = self.checkout_var.get()
        adults = self.adults_var.get()
        budget = self.budget_var.get()
        pets = 1 if self.allow_dogs_var.get() else 0
        
        # Update agent budget
        self.agent.budget_max = budget
        
        # Start thread
        thread = threading.Thread(
            target=self.run_search_thread,
            args=(cities, checkin, checkout, adults, pets)
        )
        thread.start()

    def run_search_thread(self, cities, checkin, checkout, adults, pets):
        try:
            # Run async agent in this thread
            results = asyncio.run(
                self.agent.find_best_deals(
                    cities=cities,
                    checkin=checkin,
                    checkout=checkout,
                    group_size=adults,
                    pets=pets
                )
            )
            # Schedule UI update on main thread
            self.root.after(0, self.search_complete, results)
        except Exception as e:
            print(f"Search failed: {e}")
            self.root.after(0, self.status_label.config, {"text": f"Search failed: {e}"})
            self.root.after(0, self.search_btn.state, ['!disabled'])

    def search_complete(self, results):
        count = results.get('total_deals_found', 0) if results else 0
        self.status_label.config(text=f"Search complete. Found {count} deals.")
        self.search_btn.state(['!disabled'])
        self.open_report_btn.pack(pady=10)
        
    def open_report(self):
        report_path = os.path.abspath("holland_alle_optionen.html")
        if os.path.exists(report_path):
            webbrowser.open(f"file://{report_path}")
        else:
            messagebox.showerror("Error", "Report file not found.")

if __name__ == "__main__":
    app = HollandVacationApp()
    app.root.mainloop()
