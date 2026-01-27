"""
Report Generator for Vacation Deal Finder
Generates PDF reports for search results.
"""

from fpdf import FPDF
from typing import List, Dict
from datetime import datetime
import re

class PDFReport(FPDF):
    def header(self):
        # Arial bold 15
        self.set_font('Helvetica', 'B', 15)
        # Title
        self.cell(0, 10, 'Vacation Deal Finder Report', 0, 1, 'C')
        self.ln(5)

    def footer(self):
        # Position at 1.5 cm from bottom
        self.set_y(-15)
        # Arial italic 8
        self.set_font('Helvetica', 'I', 8)
        # Page number
        self.cell(0, 10, 'Page ' + str(self.page_no()) + '/{nb}', 0, 0, 'C')

class ReportGenerator:
    def __init__(self):
        pass

    def clean_text(self, text: str) -> str:
        """Replace unsupported characters for PDF standard fonts"""
        # Simple replacement for now. FPDF2 standard fonts are Latin-1.
        # Replacing common issues.
        replacements = {
            "€": "EUR ",
            "⭐": "*",
            "🐕": "(Dog Friendly)",
            "📍": "",
            "✅": "[OK]",
            "👍": "[Good]",
            "🌤️": "",
            "🤖": "",
            "🔍": "",
            "📊": ""
        }
        for k, v in replacements.items():
            text = text.replace(k, v)
        
        # Strip other non-latin-1 characters to prevent crashes
        return text.encode('latin-1', 'replace').decode('latin-1')

    def generate_report(self, deals: List[Dict], search_params: Dict, filename: str):
        """Generate a PDF report from the deals"""
        pdf = PDFReport()
        pdf.alias_nb_pages()
        pdf.add_page()
        
        # --- Search Parameters Section ---
        pdf.set_font('Helvetica', 'B', 12)
        pdf.cell(0, 10, 'Search Parameters:', 0, 1)
        pdf.set_font('Helvetica', '', 10)
        
        params_text = [
            f"Destinations: {', '.join(search_params.get('cities', []))}",
            f"Dates: {search_params.get('checkin')} to {search_params.get('checkout')} ({search_params.get('nights')} nights)",
            f"Group: {search_params.get('group_size')} adults + {search_params.get('pets')} pet(s)",
            f"Budget Range: {search_params.get('budget_range')}"
        ]
        
        for line in params_text:
            pdf.cell(0, 6, self.clean_text(line), 0, 1)
        
        pdf.ln(5)
        
        # --- Top Deals Section ---
        pdf.set_font('Helvetica', 'B', 12)
        pdf.cell(0, 10, f"Top Deals Found ({len(deals)}):", 0, 1)
        
        for i, deal in enumerate(deals, 1):
            self._add_deal_card(pdf, i, deal)
            pdf.ln(5)
            
        try:
            pdf.output(filename)
            print(f"Report generated: {filename}")
            return True
        except Exception as e:
            print(f"Error generating PDF: {e}")
            return False

    def _add_deal_card(self, pdf: FPDF, index: int, deal: Dict):
        """Render a single deal"""
        pdf.set_fill_color(240, 240, 240)
        
        # Card Header
        pdf.set_font('Helvetica', 'B', 11)
        title = f"#{index} - {deal.get('name', 'Unknown')}"
        pdf.cell(0, 8, self.clean_text(title), 0, 1, 'L', fill=True)
        
        # Details
        pdf.set_font('Helvetica', '', 10)
        
        details = [
            f"Location: {deal.get('location')}",
            f"Price: EUR {deal.get('price_per_night')}/night",
            f"Rating: {deal.get('rating')}/5.0 ({deal.get('reviews')} reviews)",
            f"Source: {deal.get('source')}"
        ]
        
        if deal.get('pet_friendly'):
            details.append("Pet Friendly: Yes")
            
        for line in details:
            pdf.cell(0, 5, self.clean_text(line), 0, 1)
            
        # Link
        pdf.set_text_color(0, 0, 255)
        pdf.set_font('Helvetica', 'U', 9)
        link = deal.get('url', '')
        if link:
            pdf.cell(0, 5, "View Deal", 0, 1, link=link)
        
        pdf.set_text_color(0, 0, 0) # Reset color
