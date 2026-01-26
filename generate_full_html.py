#!/usr/bin/env python3
"""
Generate comprehensive HTML page with ALL vacation deals
"""
import asyncio
from holland_agent import HollandVacationAgent

async def main():
    agent = HollandVacationAgent()

    print("🔍 Searching all sources...")
    await agent.find_best_deals(
        cities=['Amsterdam', 'Rotterdam', 'Zandvoort'],
        checkin='2026-01-31',
        checkout='2026-02-01',
        group_size=4,
        pets=1
    )

    # Access all deals directly from agent
    all_deals = agent.all_deals

    # Group by source and deduplicate
    # Filter: max €100 per person (€400 total for 4 people)
    center_parcs = {}
    booking = []
    airbnb = []

    for deal in all_deals:
        source = deal.get('source', '')
        name = deal.get('name', '')
        price = deal.get('price_per_night', 0)
        price_per_person = price / 4

        # Skip if over €100 per person
        if price_per_person > 100:
            continue

        if source == 'center-parcs':
            # Deduplicate Center Parcs by name
            if name not in center_parcs:
                center_parcs[name] = deal
        elif source == 'booking.com':
            booking.append(deal)
        elif source == 'airbnb':
            airbnb.append(deal)

    center_parcs_list = list(center_parcs.values())[:5]
    booking = booking[:15]
    airbnb = airbnb[:15]

    print(f"✅ Center Parcs: {len(center_parcs_list)}")
    print(f"✅ Booking.com: {len(booking)}")
    print(f"✅ Airbnb: {len(airbnb)}")

    # Generate HTML
    html = f"""<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Holland Wochenende - Alle Optionen</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
            line-height: 1.6;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 20px;
            padding: 30px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
        }}
        h1 {{
            color: #333;
            margin-bottom: 10px;
            font-size: 2.2em;
            text-align: center;
        }}
        .subtitle {{
            color: #666;
            margin-bottom: 30px;
            font-size: 1.1em;
            text-align: center;
        }}
        .date-box {{
            background: #f8f9fa;
            padding: 15px;
            border-radius: 10px;
            margin-bottom: 30px;
            border-left: 4px solid #667eea;
        }}
        .stats {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-bottom: 30px;
        }}
        .stat-card {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 10px;
            text-align: center;
        }}
        .stat-number {{
            font-size: 2em;
            font-weight: bold;
        }}
        .stat-label {{
            font-size: 0.9em;
            opacity: 0.9;
        }}
        .category {{
            margin-bottom: 40px;
        }}
        .category-header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 15px 20px;
            border-radius: 10px;
            margin-bottom: 20px;
            font-size: 1.3em;
            font-weight: bold;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        .property-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
            gap: 20px;
        }}
        .property {{
            border: 2px solid #e9ecef;
            border-radius: 15px;
            padding: 20px;
            transition: all 0.3s;
            background: white;
        }}
        .property:hover {{
            transform: translateY(-5px);
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
            border-color: #667eea;
        }}
        .property-header {{
            margin-bottom: 15px;
        }}
        .property h3 {{
            color: #333;
            font-size: 1.2em;
            margin-bottom: 5px;
        }}
        .location {{
            color: #666;
            font-size: 0.9em;
            margin-bottom: 10px;
        }}
        .price-box {{
            background: #e7f3ff;
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 15px;
        }}
        .price {{
            font-size: 1.8em;
            font-weight: bold;
            color: #28a745;
        }}
        .price-per-person {{
            color: #666;
            font-size: 0.9em;
        }}
        .rating {{
            display: flex;
            align-items: center;
            gap: 10px;
            margin-bottom: 15px;
        }}
        .rating-value {{
            font-size: 1.3em;
            font-weight: bold;
            color: #ffc107;
        }}
        .reviews {{
            color: #666;
            font-size: 0.9em;
        }}
        .features {{
            display: flex;
            gap: 8px;
            flex-wrap: wrap;
            margin-bottom: 15px;
        }}
        .feature {{
            background: #f8f9fa;
            color: #333;
            padding: 5px 10px;
            border-radius: 15px;
            font-size: 0.85em;
        }}
        .cta-button {{
            display: block;
            background: #667eea;
            color: white;
            padding: 12px;
            border-radius: 8px;
            text-decoration: none;
            font-weight: bold;
            text-align: center;
            transition: background 0.3s;
        }}
        .cta-button:hover {{
            background: #764ba2;
        }}
        .footer {{
            text-align: center;
            margin-top: 30px;
            padding-top: 20px;
            border-top: 2px solid #e9ecef;
            color: #666;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🏖️ Holland Wochenende - Alle Optionen</h1>
        <p class="subtitle">Hundefreundliche Unterkünfte für 4 Personen + 1 Hund</p>

        <div class="date-box">
            <strong>📅 Termin:</strong> Freitag 31. Januar oder Samstag 1. Februar 2026 (1 Nacht)<br>
            <strong>👥 Gruppe:</strong> 4 Erwachsene + 1 Hund
        </div>

        <div class="stats">
            <div class="stat-card">
                <div class="stat-number">{len(center_parcs_list) + len(booking) + len(airbnb)}</div>
                <div class="stat-label">Unterkünfte gefunden</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{len(center_parcs_list)}</div>
                <div class="stat-label">Center Parcs</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{len(booking)}</div>
                <div class="stat-label">Booking.com</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{len(airbnb)}</div>
                <div class="stat-label">Airbnb</div>
            </div>
        </div>
"""

    # Center Parcs section
    if center_parcs_list:
        html += """
        <div class="category">
            <div class="category-header">
                <span>🏕️ Center Parcs - Ferienparks</span>
                <span>€42-58/Nacht</span>
            </div>
            <div class="property-grid">
"""
        for prop in center_parcs_list:
            price = prop.get('price_per_night', 0)
            per_person = price / 4
            html += f"""
                <div class="property">
                    <div class="property-header">
                        <h3>{prop.get('name', 'Property')}</h3>
                        <p class="location">📍 {prop.get('location', 'Netherlands')}</p>
                    </div>
                    <div class="price-box">
                        <div class="price">€{price}</div>
                        <div class="price-per-person">€{per_person:.2f} pro Person</div>
                    </div>
                    <div class="rating">
                        <span class="rating-value">⭐ {prop.get('rating', 0)}/5.0</span>
                        <span class="reviews">({prop.get('reviews', 0)} Bewertungen)</span>
                    </div>
                    <div class="features">
                        <span class="feature">🐕 Hunde kostenlos</span>
                        <span class="feature">🏊 Schwimmbad</span>
                        <span class="feature">🌳 Natur</span>
                    </div>
                    <a href="{prop.get('url', '#')}" class="cta-button" target="_blank">Mehr Info →</a>
                </div>
"""
        html += """
            </div>
        </div>
"""

    # Booking.com section
    if booking:
        html += """
        <div class="category">
            <div class="category-header">
                <span>🏠 Booking.com - Ferienhäuser & Apartments</span>
                <span>€50-100/Nacht</span>
            </div>
            <div class="property-grid">
"""
        for prop in booking:
            price = prop.get('price_per_night', 0)
            per_person = price / 4
            html += f"""
                <div class="property">
                    <div class="property-header">
                        <h3>{prop.get('name', 'Property')}</h3>
                        <p class="location">📍 {prop.get('location', 'Netherlands')}</p>
                    </div>
                    <div class="price-box">
                        <div class="price">€{price}</div>
                        <div class="price-per-person">€{per_person:.2f} pro Person</div>
                    </div>
                    <div class="rating">
                        <span class="rating-value">⭐ {prop.get('rating', 0)}/5.0</span>
                        <span class="reviews">({prop.get('reviews', 0)} Bewertungen)</span>
                    </div>
                    <div class="features">
                        <span class="feature">🐕 Hundefreundlich</span>
                        <span class="feature">🏖️ Strand</span>
                        <span class="feature">🍳 Küche</span>
                    </div>
                    <a href="{prop.get('url', 'https://www.booking.com')}" class="cta-button" target="_blank">Auf Booking.com ansehen →</a>
                </div>
"""
        html += """
            </div>
        </div>
"""

    # Airbnb section
    if airbnb:
        html += """
        <div class="category">
            <div class="category-header">
                <span>🏡 Airbnb - Private Unterkünfte</span>
                <span>€60-150/Nacht</span>
            </div>
            <div class="property-grid">
"""
        for prop in airbnb:
            price = prop.get('price_per_night', 0)
            per_person = price / 4
            html += f"""
                <div class="property">
                    <div class="property-header">
                        <h3>{prop.get('name', 'Property')}</h3>
                        <p class="location">📍 {prop.get('location', 'Netherlands')}</p>
                    </div>
                    <div class="price-box">
                        <div class="price">€{price}</div>
                        <div class="price-per-person">€{per_person:.2f} pro Person</div>
                    </div>
                    <div class="rating">
                        <span class="rating-value">⭐ {prop.get('rating', 0)}/5.0</span>
                        <span class="reviews">({prop.get('reviews', 0)} Bewertungen)</span>
                    </div>
                    <div class="features">
                        <span class="feature">🐕 Haustiere erlaubt</span>
                        <span class="feature">🏙️ Zentral</span>
                        <span class="feature">🌟 Einzigartig</span>
                    </div>
                    <a href="{prop.get('url', 'https://www.airbnb.com')}" class="cta-button" target="_blank">Auf Airbnb ansehen →</a>
                </div>
"""
        html += """
            </div>
        </div>
"""

    html += """
        <div class="footer">
            <p><strong>💡 Tipp:</strong> Alle Unterkünfte sind hundefreundlich</p>
            <p>Bei Center Parcs sind Hunde kostenlos (max 2), bei anderen ca. €7-15/Nacht</p>
            <p style="margin-top: 15px; font-size: 0.9em;">🤖 Erstellt mit Holland Vacation Deal Finder</p>
        </div>
    </div>
</body>
</html>
"""

    # Save HTML
    output_file = '/home/kek/Desktop/AirBnB/holland_alle_optionen.html'
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html)

    print(f"\n✅ HTML erstellt: {output_file}")
    print(f"📊 Gesamt: {len(center_parcs_list)} Center Parcs + {len(booking)} Booking.com + {len(airbnb)} Airbnb")

if __name__ == '__main__':
    asyncio.run(main())
