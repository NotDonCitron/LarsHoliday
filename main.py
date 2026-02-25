"""
CLI Entry Point for Vacation Deal Finder
Command-line interface for searching vacation deals
"""

import asyncio
import argparse
import json
import sys
from datetime import datetime, timedelta
from holland_agent import VacationAgent  # pyre-ignore[21]
from html_report_generator import HTMLReportGenerator  # pyre-ignore[21]


def parse_args():
    """Parse command-line arguments"""
    parser = argparse.ArgumentParser(
        description="Vacation Deal Finder - Find budget-friendly, dog-friendly accommodations globally",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Search Berlin for 7 nights in February
  python main.py --cities Berlin --checkin 2026-02-15 --checkout 2026-02-22

  # Search multiple destinations with budget limit
  python main.py --cities "Amsterdam,Ardennes,Winterberg" --checkin 2026-02-15 --checkout 2026-02-22 --budget-max 200

  # Search with custom group size
  python main.py --cities "Paris, France" --checkin 2026-03-01 --checkout 2026-03-08 --adults 2 --pets 1
        """
    )

    parser.add_argument(
        "--cities",
        type=str,
        required=True,
        help="Comma-separated list of cities, regions, or countries (e.g., 'Amsterdam, Berlin, Ardennes')"
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

    parser.add_argument(
        "--report",
        type=str,
        choices=["none", "html"],
        default="html",
        help="Generate report file: 'html' for VacationDeals_YYYYMMDD.html (default: html)"
    )

    parser.add_argument(
        "--schedule-minutes",
        type=int,
        default=0,
        help="Run search every N minutes (0 = run once and exit, default: 0)"
    )

    parser.add_argument(
        "--max-runs",
        type=int,
        default=0,
        help="Maximum scheduled runs (only used with --schedule-minutes, 0 = unlimited)"
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
    print("VACATION DEAL FINDER - RESULTS")
    print("="*70)

    # Search parameters
    params = results["search_params"]
    print(f"\nSearch Parameters:")
    print(f"  Destinations: {', '.join(params['cities'])}")
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

        # Direct link
        if deal.get("url"):
            print(f"  🔗 {deal['url']}")

        # Weather info if available
        if deal.get("weather_forecast"):
            weather = deal["weather_forecast"]
            if weather.get("avg_temp"):
                print(f"  Weather: {weather['avg_temp']}°C avg, {weather.get('conditions', 'N/A')}")

    print("\n" + "="*70)


async def run_once(agent: VacationAgent, args, cities, run_index: int = 1):
    """Execute one search cycle and handle output/report generation."""
    results = await agent.find_best_deals(
        cities=cities,
        checkin=args.checkin,
        checkout=args.checkout,
        group_size=args.adults,
        pets=args.pets
    )

    if args.output == "json":
        print("\n" + json.dumps(results, indent=2, ensure_ascii=False))
    else:
        print_summary(results, args.top)

    if args.report == "html":
        report_gen = HTMLReportGenerator()
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"VacationDeals_{timestamp}_run{run_index}.html"
        path = report_gen.generate_report(
            deals=results["top_10_deals"],
            search_params=results["search_params"],
            filename=filename
        )
        print(f"\n📊 Report generated: {path}")


async def main():
    """Main CLI entry point"""
    args = parse_args()

    if not validate_dates(args.checkin, args.checkout):
        sys.exit(1)

    cities = [city.strip() for city in args.cities.split(",")]

    agent = VacationAgent(
        budget_min=args.budget_min,
        budget_max=args.budget_max
    )

    try:
        interval = max(0, int(args.schedule_minutes))
        max_runs = max(0, int(args.max_runs))

        if interval == 0:
            await run_once(agent, args, cities, run_index=1)
            return

        run_count = 0
        print(f"\n⏱️ Scheduler active: every {interval} minute(s)")
        if max_runs > 0:
            print(f"   Max runs: {max_runs}")

        while True:
            run_count += 1
            started = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            print(f"\n🚀 Scheduled run #{run_count} started at {started}")

            try:
                await run_once(agent, args, cities, run_index=run_count)
            except Exception as cycle_error:
                print(f"\nRun #{run_count} failed: {cycle_error}", file=sys.stderr)

            if max_runs > 0 and run_count >= max_runs:
                print("\n✅ Scheduler finished: max runs reached")
                break

            next_run = datetime.now() + timedelta(minutes=interval)
            print(
                f"\n⏳ Waiting {interval} minute(s) until next run "
                f"({next_run.strftime('%Y-%m-%d %H:%M:%S')})"
            )
            await asyncio.sleep(float(interval * 60))

    except KeyboardInterrupt:
        print("\n\nSearch cancelled by user")
        sys.exit(130)
    except Exception as e:
        print(f"\nError: {e}", file=sys.stderr)
        sys.exit(1)
    finally:
        await agent.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
