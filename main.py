"""
CLI Entry Point for Holland Vacation Deal Finder
Command-line interface for searching vacation deals
"""

import asyncio
import argparse
import json
import sys
from datetime import datetime
from holland_agent import HollandVacationAgent


def parse_args():
    """Parse command-line arguments"""
    parser = argparse.ArgumentParser(
        description="Holland Vacation Deal Finder - Find budget-friendly, dog-friendly accommodations",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Search Amsterdam for 7 nights in February
  python main.py --cities Amsterdam --checkin 2026-02-15 --checkout 2026-02-22

  # Search multiple cities with budget limit
  python main.py --cities Amsterdam,Rotterdam,Zandvoort --checkin 2026-02-15 --checkout 2026-02-22 --budget-max 200

  # Search with custom group size
  python main.py --cities Amsterdam --checkin 2026-03-01 --checkout 2026-03-08 --adults 2 --pets 1
        """
    )

    parser.add_argument(
        "--cities",
        type=str,
        required=True,
        help="Comma-separated list of cities (e.g., 'Amsterdam,Rotterdam,Zandvoort')"
    )

    parser.add_argument(
        "--checkin",
        type=str,
        required=True,
        help="Check-in date in YYYY-MM-DD format (e.g., '2026-02-15')"
    )

    parser.add_argument(
        "--checkout",
        type=str,
        required=True,
        help="Check-out date in YYYY-MM-DD format (e.g., '2026-02-22')"
    )

    parser.add_argument(
        "--budget-min",
        type=int,
        default=40,
        help="Minimum budget per night in EUR (default: 40)"
    )

    parser.add_argument(
        "--budget-max",
        type=int,
        default=250,
        help="Maximum budget per night in EUR (default: 250)"
    )

    parser.add_argument(
        "--adults",
        type=int,
        default=4,
        help="Number of adults (default: 4)"
    )

    parser.add_argument(
        "--pets",
        type=int,
        default=1,
        help="Number of pets (default: 1)"
    )

    parser.add_argument(
        "--output",
        type=str,
        choices=["json", "summary"],
        default="json",
        help="Output format: 'json' for full data, 'summary' for human-readable (default: json)"
    )

    parser.add_argument(
        "--top",
        type=int,
        default=10,
        help="Number of top deals to show (default: 10)"
    )

    return parser.parse_args()


def validate_dates(checkin: str, checkout: str) -> bool:
    """Validate date format and logic"""
    try:
        checkin_date = datetime.strptime(checkin, "%Y-%m-%d")
        checkout_date = datetime.strptime(checkout, "%Y-%m-%d")

        if checkout_date <= checkin_date:
            print("Error: Check-out date must be after check-in date")
            return False

        if checkin_date < datetime.now():
            print("Warning: Check-in date is in the past")

        return True

    except ValueError:
        print("Error: Invalid date format. Use YYYY-MM-DD (e.g., '2026-02-15')")
        return False


def print_summary(results: dict, top_n: int):
    """Print human-readable summary"""
    print("\n" + "="*70)
    print("HOLLAND VACATION DEAL FINDER - RESULTS")
    print("="*70)

    # Search parameters
    params = results["search_params"]
    print(f"\nSearch Parameters:")
    print(f"  Cities: {', '.join(params['cities'])}")
    print(f"  Dates: {params['checkin']} to {params['checkout']} ({params['nights']} nights)")
    print(f"  Group: {params['group_size']} adults + {params['pets']} pet(s)")
    print(f"  Budget: {params['budget_range']} per night")

    # Summary
    summary = results["summary"]
    print(f"\nSearch Summary:")
    print(f"  Total properties found: {summary['total_options_found']}")
    print(f"  Dog-friendly options: {summary['dog_friendly_options']}")
    print(f"  Best overall: {summary['best_overall']}")
    print(f"  Top rated: {summary['top_rated_property']}")
    print(f"  Cheapest: {summary['cheapest_option']}")

    # Budget overview
    budget = summary["budget_overview"]
    print(f"\nPrice Range:")
    print(f"  Cheapest: €{budget['cheapest_per_night']}/night")
    print(f"  Average: €{budget['average_per_night']}/night")
    print(f"  Most expensive: €{budget['most_expensive_per_night']}/night")

    # Top deals
    print(f"\n{'='*70}")
    print(f"TOP {top_n} DEALS")
    print("="*70)

    for i, deal in enumerate(results["top_10_deals"][:top_n], 1):
        print(f"\n#{i} - {deal['name']}")
        print(f"  Location: {deal['location']}")
        print(f"  Price: €{deal['price_per_night']}/night (€{deal['total_cost_for_trip']} total)")
        print(f"  Rating: {deal['rating']}/5.0 ({deal['reviews']} reviews)")
        print(f"  Pet-friendly: {'Yes' if deal['pet_friendly'] else 'No'}")
        print(f"  Source: {deal['source']}")
        print(f"  Score: {deal['rank_score']}/100")
        print(f"  {deal['recommendation']}")

        # Weather info if available
        if deal.get("weather_forecast"):
            weather = deal["weather_forecast"]
            if weather.get("avg_temp"):
                print(f"  Weather: {weather['avg_temp']}°C avg, {weather.get('conditions', 'N/A')}")

    print("\n" + "="*70)


async def main():
    """Main CLI entry point"""
    args = parse_args()

    # Validate dates
    if not validate_dates(args.checkin, args.checkout):
        sys.exit(1)

    # Parse cities
    cities = [city.strip() for city in args.cities.split(",")]

    # Create agent
    agent = HollandVacationAgent(
        budget_min=args.budget_min,
        budget_max=args.budget_max
    )

    try:
        # Run search
        results = await agent.find_best_deals(
            cities=cities,
            checkin=args.checkin,
            checkout=args.checkout,
            group_size=args.adults,
            pets=args.pets
        )

        # Output results
        if args.output == "json":
            print("\n" + json.dumps(results, indent=2, ensure_ascii=False))
        else:
            print_summary(results, args.top)

    except KeyboardInterrupt:
        print("\n\nSearch cancelled by user")
        sys.exit(130)
    except Exception as e:
        print(f"\nError: {e}", file=sys.stderr)
        sys.exit(1)
    finally:
        agent.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
