import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime
import threading
import asyncio
import webbrowser
import os
from typing import Any
from holland_agent import VacationAgent  # pyre-ignore[21]
from favorites_manager import FavoritesManager  # pyre-ignore[21]
from favorites_manager import FavoritesManager  # pyre-ignore[21]
from report_generator import ReportGenerator  # pyre-ignore[21]
from html_report_generator import HTMLReportGenerator  # pyre-ignore[21]

class VacationApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Vacation Deal Finder")
        self.root.geometry("900x700")
        
        # Dark Theme Configuration
        self.bg_color = "#2E2E2E"
        self.fg_color = "#FFFFFF"
        self.root.configure(bg=self.bg_color)
        
        # Initialize Agent and Managers
        self.agent = VacationAgent()
        self.favorites_manager = FavoritesManager()
        self.report_generator = ReportGenerator()
        self.html_generator = HTMLReportGenerator()
        
        # Store last results
        self.current_results: Any = None
        
        # Declare GUI attributes (assigned in helper methods below)
        self.accent_color: str = ""
        self.button_color: str = ""
        self.container: Any = None
        self.main_frame: Any = None
        self.sidebar: Any = None
        self.fav_listbox: Any = None
        self.status_label: Any = None
        self.results_container: Any = None
        self.results_canvas: Any = None
        self.scrollbar: Any = None
        self.scrollable_frame: Any = None
        self.bottom_frame: Any = None
        self.open_report_btn: Any = None
        self.export_pdf_btn: Any = None
        self.log_text: Any = None
        self.cities_var: Any = None
        self.checkin_var: Any = None
        self.checkout_var: Any = None
        self.adults_var: Any = None
        self.budget_var: Any = None
        self.allow_dogs_var: Any = None
        self.dogs_check: Any = None
        self.search_btn: Any = None
        
        # Configure styles
        self.configure_styles()
        
        self.setup_ui()
        self.refresh_favorites()

    def configure_styles(self):
        style = ttk.Style()
        style.theme_use('clam')
        
        # Colors
        self.bg_color = "#2E2E2E"
        self.fg_color = "#FFFFFF"
        self.accent_color = "#4A4A4A"
        self.button_color = "#0078D4" # Standard blue
        
        style.configure("Dark.TFrame", background=self.bg_color)
        style.configure("Dark.TLabel", background=self.bg_color, foreground=self.fg_color)
        style.configure("Title.TLabel", background=self.bg_color, foreground=self.fg_color, font=("Helvetica", 18, "bold"))
        style.configure("Card.TFrame", background="#3D3D3D", relief="raised", borderwidth=1)
        
        style.configure("Dark.TButton", 
                        background=self.button_color, 
                        foreground=self.fg_color,
                        padding=10)
        style.map("Dark.TButton",
                  background=[('active', '#005A9E'), ('disabled', '#555555')])
        
        style.configure("Fav.TButton", background="#FFD700", foreground="#000000") # Gold
        
        style.configure("Dark.TCheckbutton", background=self.bg_color, foreground=self.fg_color)
        style.map("Dark.TCheckbutton",
                  background=[('active', self.bg_color)])
        
        style.configure("Dark.TEntry", fieldbackground="#3D3D3D", foreground=self.fg_color, insertcolor=self.fg_color)

    def setup_ui(self):
        # Main Container with Sidebar
        self.container = ttk.Frame(self.root, style="Dark.TFrame")
        self.container.pack(fill=tk.BOTH, expand=True)
        
        # Left Side (Search Area)
        self.main_frame = ttk.Frame(self.container, style="Dark.TFrame")
        self.main_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Right Side (Sidebar)
        self.sidebar = ttk.Frame(self.container, width=250, style="Dark.TFrame")
        self.sidebar.pack(side=tk.RIGHT, fill=tk.Y, padx=(0, 20), pady=20)
        
        # Sidebar Content
        ttk.Label(self.sidebar, text="⭐ Favorites", style="Title.TLabel", font=("Helvetica", 14, "bold")).pack(pady=(0, 10))
        
        self.fav_listbox = tk.Listbox(
            self.sidebar, 
            bg="#3D3D3D", 
            fg="#FFFFFF", 
            selectbackground="#0078D4",
            borderwidth=0,
            highlightthickness=0,
            font=("Helvetica", 10)
        )
        self.fav_listbox.pack(fill=tk.BOTH, expand=True, pady=10)
        self.fav_listbox.bind("<Double-Button-1>", self.open_favorite)
        
        ttk.Button(self.sidebar, text="Remove Selected", style="Dark.TButton", command=self.remove_selected_favorite).pack(fill=tk.X)
        
        # Title
        title_label = ttk.Label(
            self.main_frame, 
            text="🏖️ Vacation Deal Finder", 
            style="Title.TLabel"
        )
        title_label.pack(pady=(0, 20))
        
        self.create_input_form()
        
        # Status Area
        self.status_label = ttk.Label(self.main_frame, text="", style="Dark.TLabel")
        self.status_label.pack(pady=10)
        
        # Results Scrollable Area
        self.results_container = ttk.Frame(self.main_frame, style="Dark.TFrame")
        self.results_container.pack(fill=tk.BOTH, expand=True)
        
        self.results_canvas = tk.Canvas(self.results_container, bg=self.bg_color, highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(self.results_container, orient="vertical", command=self.results_canvas.yview)
        self.scrollable_frame = ttk.Frame(self.results_canvas, style="Dark.TFrame")

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.results_canvas.configure(
                scrollregion=self.results_canvas.bbox("all")
            )
        )

        self.results_canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.results_canvas.configure(yscrollcommand=self.scrollbar.set)

        self.results_canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        # --- LOG WINDOW ---
        ttk.Label(self.main_frame, text="📜 Activity Log:", style="Dark.TLabel").pack(pady=(10, 0), anchor="w")
        self.log_text = tk.Text(
            self.main_frame, 
            height=6, 
            bg="#1E1E1E", 
            fg="#00FF00", # Matrix green
            font=("Consolas", 9),
            state=tk.DISABLED
        )
        self.log_text.pack(fill=tk.X, pady=(5, 10))
        
        # Redirect stdout
        import sys
        class RedirectStdout:
            def __init__(self, text_widget, root):
                self.text_widget = text_widget
                self.root = root
            def write(self, string):
                self.root.after(0, self._write, string)
            def _write(self, string):
                self.text_widget.config(state=tk.NORMAL)
                self.text_widget.insert(tk.END, string)
                self.text_widget.see(tk.END)
                self.text_widget.config(state=tk.DISABLED)
            def flush(self):
                pass
        
        sys.stdout = RedirectStdout(self.log_text, self.root)
        
        # Bottom Buttons Frame
        self.bottom_frame = ttk.Frame(self.main_frame, style="Dark.TFrame")
        self.bottom_frame.pack(pady=10, fill=tk.X)
        
        self.open_report_btn = ttk.Button(
            self.bottom_frame,
            text="📄 Open HTML Report",
            style="Dark.TButton",
            command=self.open_report
        )
        # Hidden initially
        
        self.export_pdf_btn = ttk.Button(
            self.bottom_frame,
            text="💾 Export PDF",
            style="Dark.TButton",
            command=self.export_pdf
        )
        # Hidden initially

    def create_input_form(self):
        # Form Container
        form_frame = ttk.Frame(self.main_frame, style="Dark.TFrame")
        form_frame.pack(fill=tk.X, pady=10)
        
        # Grid Configuration
        form_frame.columnconfigure(1, weight=1)
        
        # Helper for form rows
        def add_row(label_text, var, row):
            ttk.Label(form_frame, text=label_text, style="Dark.TLabel").grid(row=row, column=0, sticky="w", pady=8)
            entry = ttk.Entry(form_frame, textvariable=var)
            entry.grid(row=row, column=1, sticky="ew", padx=(15, 0))
            return entry

        # --- Destinations ---
        self.cities_var = tk.StringVar(value="Amsterdam, Berlin, Ardennes")
        add_row("Destinations (comma-separated):", self.cities_var, 0)
        
        # --- Dates ---
        self.checkin_var = tk.StringVar(value="2026-02-15")
        add_row("Check-in (YYYY-MM-DD):", self.checkin_var, 1)
        
        self.checkout_var = tk.StringVar(value="2026-02-22")
        add_row("Check-out (YYYY-MM-DD):", self.checkout_var, 2)
        
        # --- Group & Budget ---
        self.adults_var = tk.IntVar(value=4)
        add_row("Number of Adults:", self.adults_var, 3)
        
        self.budget_var = tk.IntVar(value=250)
        add_row("Max Budget (€/night):", self.budget_var, 4)
        
        # --- Pet Toggle ---
        self.allow_dogs_var = tk.BooleanVar(value=True)
        self.dogs_check = ttk.Checkbutton(
            form_frame, 
            text="🐕 Allow Dogs (Hundefreundlich)", 
            variable=self.allow_dogs_var,
            style="Dark.TCheckbutton"
        )
        self.dogs_check.grid(row=5, column=0, columnspan=2, sticky="w", pady=15)
        
        # --- Search Button ---
        self.search_btn = ttk.Button(
            self.main_frame,
            text="🔍 Search Best Deals",
            style="Dark.TButton",
            command=self.start_search
        )
        self.search_btn.pack(pady=10, fill=tk.X)

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
        except ValueError:
            messagebox.showerror("Invalid Date Format", "Please use YYYY-MM-DD format.")
            return False
        return True

    def start_search(self):
        if not self.validate_inputs():
            return
        
        self.status_label.config(text="Starting search... Please wait.")
        self.search_btn.state(['disabled'])
        self.open_report_btn.pack_forget()
        self.export_pdf_btn.pack_forget()
        
        # Clear previous results
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        
        cities = [c.strip() for c in self.cities_var.get().split(",")]
        checkin = self.checkin_var.get()
        checkout = self.checkout_var.get()
        adults = self.adults_var.get()
        budget = self.budget_var.get()
        pets = 1 if self.allow_dogs_var.get() else 0
        
        self.agent.budget_max = budget
        
        thread = threading.Thread(
            target=self.run_search_thread,
            args=(cities, checkin, checkout, adults, pets)
        )
        thread.start()

    def run_search_thread(self, cities, checkin, checkout, adults, pets):
        try:
            results = asyncio.run(
                self.agent.find_best_deals(
                    cities=cities,
                    checkin=checkin,
                    checkout=checkout,
                    group_size=adults,
                    pets=pets
                )
            )
            self.root.after(0, self.search_complete, results)
        except Exception as e:
            self.root.after(0, self.status_label.config, {"text": f"Search failed: {e}"})
            self.root.after(0, self.search_btn.state, ['!disabled'])

    def search_complete(self, results):
        self.current_results = results # Store results
        count = results.get('total_deals_found', 0) if results else 0
        self.status_label.config(text=f"Search complete. Found {count} deals.")
        self.search_btn.state(['!disabled'])
        
        # Generate HTML Report automatically for the current search
        self._generate_html_report(results)
        
        # Show buttons
        self.open_report_btn.pack(side=tk.LEFT, padx=10)
        self.export_pdf_btn.pack(side=tk.LEFT, padx=10)
        
        # Populate results list
        top_deals = results.get('top_10_deals', [])
        for deal in top_deals:
            self.add_deal_card(deal)

    def _generate_html_report(self, results):
        """Generate a fresh HTML report using the improved generator"""
        params = results.get('search_params', {})
        deals = results.get('top_10_deals', [])
        
        # Use new generator
        self.html_generator.generate_report(
            deals=deals,
            search_params=params,
            filename="last_search_report.html"
        )

    def open_report(self):
        report_path = os.path.abspath("last_search_report.html")
        if os.path.exists(report_path):
            webbrowser.open(f"file://{report_path}")
        else:
            messagebox.showerror("Error", "Report file not found. Please run a search first.")

    def export_pdf(self):
        if not self.current_results:
            messagebox.showerror("Error", "No search results to export.")
            return

        filename = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF Documents", "*.pdf")],
            initialfile=f"vacation_deals_{datetime.now().strftime('%Y%m%d')}.pdf"
        )
        
        if filename:
            success = self.report_generator.generate_report(
                self.current_results.get('top_10_deals', []),
                self.current_results.get('search_params', {}),
                filename
            )
            if success:
                messagebox.showinfo("Success", f"Report saved to {filename}")
                webbrowser.open(f"file://{filename}")
            else:
                messagebox.showerror("Error", "Failed to generate report.")

    def refresh_favorites(self):
        """Refresh the favorites listbox"""
        self.fav_listbox.delete(0, tk.END)
        favorites = self.favorites_manager.get_all()
        for fav in favorites:
            self.fav_listbox.insert(tk.END, fav.get('name', 'Unknown'))

    def open_favorite(self, event):
        """Open selected favorite in browser"""
        selection = self.fav_listbox.curselection()
        if selection:
            index = selection[0]
            favorites = self.favorites_manager.get_all()
            if index < len(favorites):
                url = favorites[index].get('url')
                if url:
                    webbrowser.open(url)

    def remove_selected_favorite(self):
        """Remove selected favorite from list"""
        selection = self.fav_listbox.curselection()
        if selection:
            index = selection[0]
            favorites = self.favorites_manager.get_all()
            if index < len(favorites):
                self.favorites_manager.remove(favorites[index].get('id'))
                self.refresh_favorites()

    def add_deal_card(self, deal):
        """Add a deal card to the results area"""
        card = ttk.Frame(self.scrollable_frame, style="Card.TFrame")
        card.pack(fill=tk.X, pady=5, padx=5)
        
        # Deal name
        name_label = ttk.Label(
            card, 
            text=deal.get('name', 'Unknown'), 
            style="Dark.TLabel",
            font=("Helvetica", 12, "bold")
        )
        name_label.pack(anchor="w", padx=10, pady=(10, 0))
        
        # Deal details
        details = f"📍 {deal.get('location', 'N/A')} | ⭐ {deal.get('rating', 'N/A')}/5 | €{deal.get('price_per_night', 'N/A')}/night"
        source = deal.get('source', 'unknown')
        details += f" | 🔍 {source}"
        details_label = ttk.Label(card, text=details, style="Dark.TLabel")
        details_label.pack(anchor="w", padx=10)
        
        # Recommendation
        rec = deal.get('recommendation', '')
        if rec:
            rec_label = ttk.Label(card, text=rec, style="Dark.TLabel", foreground="#28a745")
            rec_label.pack(anchor="w", padx=10, pady=(0, 10))
        
        # Open button
        url = deal.get('url')
        if url:
            open_btn = ttk.Button(
                card,
                text="Open in Browser",
                style="Dark.TButton",
                command=lambda u=url: webbrowser.open(u)  # pyre-ignore[6]
            )
            open_btn.pack(anchor="e", padx=10, pady=(0, 10))

if __name__ == "__main__":
    app = VacationApp()
    app.root.mainloop()
