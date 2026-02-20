"""
HTML Report Generator for Vacation Deal Finder
Generates a standalone, beautiful HTML report for vacation deals.
"""

import os
from typing import List, Dict
from datetime import datetime

class HTMLReportGenerator:
    def __init__(self):
        pass

    def generate_report(self, deals: List[Dict], search_params: Dict, filename: str = "vacation_report.html") -> str:
        """
        Generate a comprehensive HTML report.
        
        Args:
            deals: List of deal dictionaries.
            search_params: Search parameters used.
            filename: Output filename.
            
        Returns:
            Absolute path to the generated report file.
        """
        
        # Categorize deals
        center_parcs = [d for d in deals if d.get('source') == 'center-parcs']
        booking = [d for d in deals if 'booking.com' in d.get('source', '').lower()]
        airbnb = [d for d in deals if 'airbnb' in d.get('source', '').lower()]
        others = [d for d in deals if d not in center_parcs and d not in booking and d not in airbnb]
        
        # Add others to booking temporarily if source is unknown, just for display consistency
        booking.extend(others)

        html_content = self._build_html(search_params, center_parcs, booking, airbnb, len(deals))
        
        with open(filename, "w", encoding="utf-8") as f:
            f.write(html_content)
            
        return os.path.abspath(filename)

    def _build_html(self, params: Dict, center_parcs: List[Dict], booking: List[Dict], airbnb: List[Dict], total_count: int) -> str:
        """Construct the HTML string."""
        
        # Improve parameter display
        cities_str = ", ".join(params.get('cities', []))
        checkin_fmt = params.get('checkin', '')
        checkout_fmt = params.get('checkout', '')
        nights = params.get('nights', 0)
        
        styles = """
            body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f4f7f6; color: #333; margin: 0; padding: 20px; line-height: 1.6; }
            .container { max-width: 1200px; margin: 0 auto; background: white; border-radius: 12px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); overflow: hidden; }
            header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; }
            header h1 { margin: 0; font-size: 2.5em; }
            header p { margin: 10px 0 0; font-size: 1.1em; opacity: 0.9; }
            
            .summary-box { background: #f8f9fa; margin: 20px; padding: 20px; border-radius: 8px; border-left: 5px solid #667eea; display: flex; flex-wrap: wrap; gap: 20px; justify-content: space-between; }
            .summary-item strong { display: block; font-size: 0.9em; color: #666; text-transform: uppercase; margin-bottom: 5px; }
            .summary-item span { font-size: 1.2em; font-weight: bold; color: #333; }

            .section-title { padding: 20px 20px 10px; font-size: 1.5em; font-weight: bold; color: #333; border-bottom: 2px solid #eee; margin-bottom: 15px; display: flex; align-items: center; gap: 10px; }
            .badge { background: #667eea; color: white; padding: 2px 8px; border-radius: 12px; font-size: 0.6em; vertical-align: middle; }
            
            .grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 20px; padding: 0 20px 20px; }
            .card { background: white; border: 1px solid #e1e4e8; border-radius: 10px; overflow: hidden; transition: transform 0.2s, box-shadow 0.2s; display: flex; flex-direction: column; }
            .card:hover { transform: translateY(-5px); box-shadow: 0 10px 20px rgba(0,0,0,0.1); border-color: #667eea; }
            
            .card-body { padding: 15px; flex-grow: 1; }
            .card-title { font-size: 1.1em; font-weight: bold; margin: 0 0 10px; color: #2c3e50; line-height: 1.3; }
            .card-location { font-size: 0.9em; color: #7f8c8d; margin-bottom: 10px; display: flex; align-items: center; gap: 5px; }
            
            .card-stats { display: flex; justify-content: space-between; margin-bottom: 10px; font-size: 0.9em; }
            .rating { color: #f1c40f; font-weight: bold; }
            .reviews { color: #95a5a6; font-size: 0.9em; margin-left: 5px; }
            
            .price-tag { font-size: 1.4em; font-weight: bold; color: #27ae60; margin: 10px 0; }
            .price-sub { font-size: 0.6em; color: #7f8c8d; font-weight: normal; }
            
            .tags { display: flex; flex-wrap: wrap; gap: 5px; margin-bottom: 15px; }
            .tag { background: #e8f4fd; color: #3498db; padding: 3px 8px; border-radius: 4px; font-size: 0.8em; }
            .tag.pet { background: #e8f8f5; color: #2ecc71; }
            
            .btn { display: block; background: #667eea; color: white; text-align: center; padding: 10px; text-decoration: none; border-radius: 6px; font-weight: bold; margin-top: auto; transition: background 0.2s; }
            .btn:hover { background: #5a67d8; }
            
            footer { text-align: center; padding: 20px; color: #95a5a6; font-size: 0.9em; border-top: 1px solid #eee; margin-top: 20px; }
        """
        
        html = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Vacation Deals Report</title>
            <style>{styles}</style>
        </head>
        <body>
            <div class="container">
                <header>
                    <h1>🏖️ Vacation Deals Report</h1>
                    <p>Generated on {datetime.now().strftime('%Y-%m-%d %H:%M')}</p>
                </header>
                
                <div class="summary-box">
                    <div class="summary-item">
                        <strong>Destinations</strong>
                        <span>{cities_str}</span>
                    </div>
                    <div class="summary-item">
                        <strong>Dates</strong>
                        <span>{checkin_fmt} to {checkout_fmt} ({nights} nights)</span>
                    </div>
                    <div class="summary-item">
                        <strong>Travelers</strong>
                        <span>{params.get('group_size', '?')} Adults + {params.get('pets', '?')} Pets</span>
                    </div>
                    <div class="summary-item">
                        <strong>Total Found</strong>
                        <span>{total_count} Properties</span>
                    </div>
                </div>
        """
        
        # Helper for sections
        def add_section(title, icon, items):
            if not items: return ""
            section_html = f'<div class="section-title"><span>{icon} {title}</span> <span class="badge">{len(items)}</span></div><div class="grid">'
            for item in items:
                section_html += self._render_card(item)
            section_html += '</div>'
            return section_html
            
        html += add_section("Center Parcs", "🏕️", center_parcs)
        html += add_section("Booking.com & Others", "🏠", booking)
        html += add_section("Airbnb", "🏡", airbnb)
        
        html += """
                <footer>
                    generated by Vacation Deal Finder &bull; Offline Report
                </footer>
            </div>
        </body>
        </html>
        """
        
        return html

    def _render_card(self, item: Dict) -> str:
        price = item.get('price_per_night', 0)
        rating = item.get('rating', 0)
        reviews = item.get('reviews', 0)
        name = item.get('name', 'Unknown Property')
        location = item.get('location', 'Unknown Location')
        url = item.get('url', '#')
        
        pet_badge = ""
        if item.get('pet_friendly'):
            pet_badge = '<span class="tag pet">🐕 Pet Friendly</span>'
            
        return f"""
            <div class="card">
                <div class="card-body">
                    <div class="card-location">📍 {location}</div>
                    <div class="card-title">{name}</div>
                    
                    <div class="card-stats">
                        <span class="rating">⭐ {rating}/5.0</span>
                        <span class="reviews">({reviews} reviews)</span>
                    </div>
                    
                    <div class="price-tag">
                        €{price} <span class="price-sub">/ night</span>
                    </div>
                    
                    <div class="tags">
                        {pet_badge}
                    </div>
                    
                    <a href="{url}" target="_blank" class="btn">View Deal →</a>
                </div>
            </div>
        """
