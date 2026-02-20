# Holland Vacation Deal Finder

AI-powered vacation deal finder for Netherlands. Finds budget-friendly, dog-friendly accommodations for families.

## Features

- **Multi-source search**: Booking.com, Airbnb, Center Parcs
- **Dog-friendly filter**: Only shows pet-friendly accommodations
- **Weather integration**: Ranks deals based on weather forecasts
- **Smart ranking**: Multi-factor scoring algorithm
- **Parallel search**: Searches multiple cities simultaneously
- **Browser automation**: Uses agent-browser CLI for web scraping

## Requirements

- Python 3.8+
- Node.js (for agent-browser)
- agent-browser CLI installed

## Installation

```bash
# Install Python dependencies
pip install -r requirements.txt

# Install agent-browser (if not already installed)
npm install -g @vercel/agent-browser
```

## Configuration

Create a `.env` file with your API keys:

```bash
FIRECRAWL_API_KEY=your_firecrawl_key_here
OPENWEATHER_API_KEY=your_openweather_key_here
AGENT_BROWSER_SESSION=holland-deals
AGENT_BROWSER_PATH=/path/to/agent-browser
```

### Getting API Keys

- **OpenWeather API**: Free at https://openweathermap.org/api (1,000 calls/day)
- **Firecrawl API**: Optional, for enhanced scraping at https://firecrawl.dev

## Usage

### Basic Search

```bash
python main.py \
  --cities Amsterdam \
  --checkin 2026-02-15 \
  --checkout 2026-02-22
```

### Multi-City Search

```bash
python main.py \
  --cities "Amsterdam,Rotterdam,Zandvoort" \
  --checkin 2026-02-15 \
  --checkout 2026-02-22 \
  --budget-max 200
```

### Custom Group Size

```bash
python main.py \
  --cities Amsterdam \
  --checkin 2026-03-01 \
  --checkout 2026-03-08 \
  --adults 2 \
  --pets 1
```

### Human-Readable Output

```bash
python main.py \
  --cities Amsterdam \
  --checkin 2026-02-15 \
  --checkout 2026-02-22 \
  --output summary \
  --top 5
```

## Command-Line Options

| Option | Description | Default |
|--------|-------------|---------|
| `--cities` | Comma-separated city list (required) | - |
| `--checkin` | Check-in date YYYY-MM-DD (required) | - |
| `--checkout` | Check-out date YYYY-MM-DD (required) | - |
| `--budget-min` | Minimum budget per night (EUR) | 40 |
| `--budget-max` | Maximum budget per night (EUR) | 250 |
| `--adults` | Number of adults | 4 |
| `--pets` | Number of pets | 1 |
| `--output` | Output format: json or summary | json |
| `--top` | Number of top deals to show | 10 |

## Scoring Algorithm

Deals are ranked using a multi-factor scoring system:

- **Price Score** (0-40 points): Lower price = higher score
- **Rating Score** (0-30 points): Based on property rating
- **Review Count** (0-20 points): More reviews = more trustworthy
- **Dog-Friendly Multiplier**: 1.4x bonus for pet-friendly properties
- **Weather Bonus**: 1.2x bonus if average temperature > 15°C

## Architecture

```
holland_agent.py          # Main orchestrator
├── booking_scraper.py    # Booking.com integration
├── airbnb_scraper.py     # Airbnb integration
├── weather_integration.py # OpenWeather API
└── deal_ranker.py        # Scoring system
```

## Data Sources

1. **Booking.com**: Live search with pet-friendly filter
2. **Airbnb**: Pet-allowed homes search
3. **Center Parcs**: Static data for popular Dutch vacation parks
4. **OpenWeather**: 5-day weather forecasts

## Example Output

```json
{
  "timestamp": "2026-01-25T18:00:00",
  "search_params": {
    "cities": ["Amsterdam", "Rotterdam"],
    "checkin": "2026-02-15",
    "checkout": "2026-02-22",
    "nights": 7,
    "group_size": 4,
    "pets": 1
  },
  "total_deals_found": 15,
  "top_10_deals": [
    {
      "rank_score": 89.2,
      "name": "Center Parcs Zandvoort Beach",
      "location": "Zandvoort aan Zee",
      "price_per_night": 58,
      "total_cost_for_trip": 406,
      "rating": 4.5,
      "reviews": 512,
      "pet_friendly": true,
      "recommendation": "🔥 EXCELLENT | €406 total"
    }
  ],
  "summary": {
    "best_overall": "Center Parcs Zandvoort Beach",
    "dog_friendly_options": 15,
    "total_options_found": 15
  }
}
```

## Troubleshooting

### Agent-browser not found

Make sure agent-browser is installed and the path in `.env` is correct:

```bash
which agent-browser
# Update AGENT_BROWSER_PATH in .env with the output
```

### Weather API errors

Check your OpenWeather API key is valid and you haven't exceeded rate limits (60 calls/min on free tier).

### No results found

Try:
- Expanding date range
- Increasing budget-max
- Trying different cities
- Checking if dates are in the future

## Development

### Running Tests

```bash
# Test with example search
python holland_agent.py

# Test CLI
python main.py --cities Amsterdam --checkin 2026-02-15 --checkout 2026-02-22 --output summary
```

### Project Structure

```
/home/kek/Desktop/AirBnB/
├── .claude/              # Claude Code project context
├── .env                  # API keys (not in git)
├── .gitignore           # Git ignore rules
├── requirements.txt     # Python dependencies
├── main.py             # CLI entry point
├── holland_agent.py    # Main orchestrator
├── booking_scraper.py  # Booking.com scraper
├── airbnb_scraper.py   # Airbnb scraper
├── deal_ranker.py      # Scoring algorithm
├── weather_integration.py # Weather API
└── README.md           # This file
```

## Tips for Best Deals

1. **Weekdays are cheaper**: Tuesday-Thursday can be 30% cheaper than weekends
2. **Avoid school holidays**: Book just before or after holiday periods
3. **Last-minute deals**: 7 days before travel often has best prices
4. **Center Parcs**: Dogs stay free at most locations
5. **Weather matters**: Spring/summer have better weather bonus

## License

MIT

## Contributing

This is a personal project. Feel free to fork and adapt for your needs.
