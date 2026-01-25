# Quick Start Guide

## Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Or use the virtual environment
source venv/bin/activate
```

## Basic Usage

### Single City Search
```bash
python3 main.py \
  --cities Amsterdam \
  --checkin 2026-02-15 \
  --checkout 2026-02-22 \
  --output summary
```

### Multi-City Search
```bash
python3 main.py \
  --cities "Amsterdam,Rotterdam,Zandvoort" \
  --checkin 2026-02-15 \
  --checkout 2026-02-22 \
  --budget-max 200 \
  --output summary
```

### JSON Output (for automation)
```bash
python3 main.py \
  --cities Amsterdam \
  --checkin 2026-02-15 \
  --checkout 2026-02-22 \
  > results.json
```

## Key Features

- **Dog-friendly only**: All results are pet-friendly
- **Multi-source**: Searches Booking.com, Airbnb, Center Parcs
- **Weather integration**: Ranks deals based on forecasts
- **Smart scoring**: Price + rating + reviews + weather
- **Parallel search**: Fast multi-city searches

## Output Formats

### Summary (Human-readable)
```bash
--output summary --top 5
```
Shows formatted results with recommendations.

### JSON (Machine-readable)
```bash
--output json
```
Full structured data for automation.

## Common Searches

### Weekend Trip (3 nights)
```bash
python3 main.py --cities Zandvoort --checkin 2026-03-14 --checkout 2026-03-17
```

### Week-long Vacation
```bash
python3 main.py --cities "Amsterdam,Utrecht" --checkin 2026-04-01 --checkout 2026-04-08
```

### Budget Search
```bash
python3 main.py --cities Amsterdam --checkin 2026-02-15 --checkout 2026-02-22 --budget-max 100
```

### Small Group
```bash
python3 main.py --cities Rotterdam --checkin 2026-03-01 --checkout 2026-03-08 --adults 2 --pets 1
```

## Tips

1. **Best prices**: Search 2-4 weeks in advance
2. **Avoid weekends**: Weekday stays are cheaper
3. **Multiple cities**: Compare prices across regions
4. **Weather bonus**: Spring/summer dates get higher scores
5. **Center Parcs**: Dogs stay free at most locations

## Scoring System

- **Price**: 0-40 points (cheaper = better)
- **Rating**: 0-30 points (higher rating = better)
- **Reviews**: 0-20 points (more reviews = better)
- **Dog-friendly**: 1.4x multiplier
- **Weather**: 1.2x bonus if temp > 15°C

## Troubleshooting

### No results found
- Increase `--budget-max`
- Try different cities
- Check dates are in the future

### Weather API errors
- Verify `OPENWEATHER_API_KEY` in `.env`
- Check rate limits (60 calls/min free tier)

### Agent-browser warnings
- Normal - system uses fallback data
- Live scraping requires browser setup
