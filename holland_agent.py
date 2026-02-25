"""
Vacation Deal Finder Agent - Main Orchestrator
AI-powered vacation deal finder for any destination.

Key improvements:
- Parallel cross-source scraping (Booking + Airbnb simultaneously)
- Parallel cross-city scraping with staggered start times
- Central validation before ranking
- Observability with run IDs and KPI counters
- Health reporting after search
"""

import asyncio
import hashlib
import json
import os
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv  # pyre-ignore[21]

from booking_scraper import BookingScraper  # pyre-ignore[21]
from deal_ranker import DealRanker  # pyre-ignore[21]
from observability import observability_tracker  # pyre-ignore[21]
from patchright_airbnb_scraper import PatchrightAirbnbScraper as SmartAirbnbScraper
from rate_limit_bypass import cache, price_alerts  # pyre-ignore[21]
from scraper_health import health_reporter, scraper_metrics  # pyre-ignore[21]
from weather_integration import WeatherIntegration  # pyre-ignore[21]

load_dotenv()


class VacationAgent:
    """Main agent that orchestrates vacation deal search across multiple sources."""

    def __init__(self, budget_min: int = 40, budget_max: int = 250):
        self.budget_min = budget_min
        self.budget_max = budget_max
        self.booking_scraper = BookingScraper()
        self.airbnb_scraper = SmartAirbnbScraper()
        self.weather = WeatherIntegration()

        if not os.getenv("OPENWEATHER_API_KEY"):
            print("   ⚠️ WARNUNG: OPENWEATHER_API_KEY fehlt in Umgebungsvariablen!")

        self.ranker = DealRanker(budget_max=budget_max)
        self.all_deals: List[Dict[str, Any]] = []
        self.cache = cache
        self.last_run_summary: Dict[str, Any] = {}
        self.last_validation: Dict[str, Any] = {}

    async def find_best_deals(
        self,
        cities: List[str],
        checkin: str,
        checkout: str,
        group_size: int = 4,
        children: int = 0,
        pets: int = 1,
        budget: int = 250,
        budget_type: str = "night",
    ) -> Dict[str, Any]:
        """Main method - finds, validates and ranks vacation deals."""
        run_id = observability_tracker.start_run(
            component="vacation_agent.find_best_deals",
            params={
                "cities": cities,
                "checkin": checkin,
                "checkout": checkout,
                "group_size": group_size,
                "children": children,
                "pets": pets,
                "budget": budget,
                "budget_type": budget_type,
            },
        )

        try:
            d1 = datetime.strptime(checkin, "%Y-%m-%d")
            d2 = datetime.strptime(checkout, "%Y-%m-%d")
            nights = max(1, (d2 - d1).days)

            if budget_type == "total":
                self.budget_max = round(budget / nights)
            else:
                self.budget_max = budget

            self.ranker.budget_max = self.budget_max

            observability_tracker.set_attr(run_id, "nights", nights)
            observability_tracker.set_attr(run_id, "budget_max", self.budget_max)

            print("\n🤖 Vacation Deal Finder")
            print(f"   Run-ID: {run_id}")
            print(f"   Destinations: {', '.join(cities)}")
            print(f"   Dates: {checkin} → {checkout} ({nights} nights)")
            print(f"   Group: {group_size} adults, {children} children, {pets} dog(s)")
            print(f"   Budget: €{self.budget_max}/night (Calculated from {budget} {budget_type})\n")

            print("🔍 Searching accommodations...")

            async def _search_with_delay(city: str, delay: float) -> List[Dict[str, Any]]:
                """Search a city with initial delay for stagger and cache check."""
                cache_key = self.cache.make_key(
                    "agent_search",
                    city=city,
                    checkin=checkin,
                    checkout=checkout,
                    group_size=group_size,
                    pets=pets,
                    budget_max=self.budget_max,
                )

                cached = self.cache.get(cache_key)
                if isinstance(cached, list):
                    observability_tracker.incr(run_id, "cache_hits")
                    observability_tracker.event(run_id, "city_cache_hit", city=city, deal_count=len(cached))
                    cached_copy: List[Dict[str, Any]] = []
                    for item in cached:
                        deal = dict(item)
                        if " (cache)" not in deal.get("source", ""):
                            deal["source"] = deal.get("source", "unknown") + " (cache)"
                        cached_copy.append(deal)
                    return cached_copy

                observability_tracker.incr(run_id, "cache_misses")

                if delay > 0:
                    await asyncio.sleep(delay)

                deals = await self._search_single_city(
                    city, checkin, checkout, nights, group_size, children, pets
                )

                if deals:
                    self.cache.set(cache_key, deals)
                    observability_tracker.incr(run_id, "cache_sets")
                    observability_tracker.event(run_id, "city_search_success", city=city, deal_count=len(deals))
                else:
                    observability_tracker.event(run_id, "city_search_empty", city=city)

                return deals

            tasks = [_search_with_delay(city, idx * 2.0) for idx, city in enumerate(cities)]
            results_per_city = await asyncio.gather(*tasks, return_exceptions=True)

            final_results: List[List[Dict[str, Any]]] = []
            for idx, result in enumerate(results_per_city):
                city = cities[idx]
                if isinstance(result, list):
                    final_results.append(result)
                else:
                    observability_tracker.incr(run_id, "city_failures")
                    observability_tracker.event(
                        run_id,
                        "city_search_error",
                        city=city,
                        error=self._truncate_text(result, 180),
                    )
                    print(f"   ⚠️ Error searching {city}: {self._truncate_text(result, 100)}")
                    final_results.append([])

            self.all_deals = []
            for deals_list in final_results:
                self.all_deals.extend(deals_list)

            raw_count = len(self.all_deals)
            observability_tracker.incr(run_id, "deals_raw", float(raw_count))

            validation = self._validate_deals(pets)
            self.last_validation = validation
            observability_tracker.incr(run_id, "deals_valid", float(validation.get("valid_count", 0)))
            observability_tracker.set_attr(run_id, "validation", validation)

            print(f"   Found {len(self.all_deals)} valid properties\n")

            print("🔔 Checking for price drops...")
            alert_msgs: List[str] = []
            for deal in self.all_deals:
                prop_seed = str(deal.get("url") or deal.get("name") or "")
                prop_hash = hashlib.md5(prop_seed.encode("utf-8")).hexdigest()
                prop_id = "".join(prop_hash[i] for i in range(12))

                threshold_override = deal.get("alert_threshold")
                threshold: Optional[float] = None
                if isinstance(threshold_override, (int, float)):
                    threshold = float(threshold_override)

                cooldown_override = deal.get("alert_cooldown_minutes")
                cooldown_minutes: Optional[int] = None
                if isinstance(cooldown_override, int) and cooldown_override >= 0:
                    cooldown_minutes = cooldown_override

                triggered, msg = price_alerts.track_property(
                    property_id=prop_id,
                    name=deal.get("name", "Unknown"),
                    price=float(deal.get("price_per_night", 0)),
                    url=deal.get("url", ""),
                    source=deal.get("source", "unknown"),
                    threshold=threshold,
                    cooldown_minutes=cooldown_minutes,
                )

                history = price_alerts.get_history(prop_id)
                if len(history) >= 2:
                    previous_raw = history[-2].get("price")
                    current_raw = history[-1].get("price")
                    previous = self._safe_float(previous_raw, default=0.0)
                    current = self._safe_float(current_raw, default=0.0)

                    if previous > 0 and current > 0:
                        delta_percent = ((current - previous) / previous) * 100.0
                        deal["price_delta_percent"] = float(f"{delta_percent:.2f}")
                        if delta_percent <= -0.5:
                            deal["price_trend"] = "down"
                        elif delta_percent >= 0.5:
                            deal["price_trend"] = "up"
                        else:
                            deal["price_trend"] = "stable"

                if triggered:
                    alert_msgs.append(msg)
                    observability_tracker.incr(run_id, "price_alerts_triggered")
                    print(msg)

            if not alert_msgs:
                print("   No significant price drops detected since last search.")

            print("🌤️  Fetching weather forecasts...")
            self.all_deals = await self.weather.enrich_deals_with_weather(self.all_deals, cities)

            print("📊 Ranking deals...\n")
            ranked = self.ranker.rank_deals(self.all_deals, nights)

            airbnb_deals = [d for d in ranked if "airbnb" in d.get("source", "").lower()]
            booking_deals = [d for d in ranked if "booking" in d.get("source", "").lower()]
            summary = self.ranker.generate_summary(ranked, nights)

            print(health_reporter.generate())

            observability_tracker.set_attr(run_id, "total_deals_found", len(self.all_deals))
            observability_tracker.set_attr(run_id, "airbnb_deals", len(airbnb_deals))
            observability_tracker.set_attr(run_id, "booking_deals", len(booking_deals))
            observability_tracker.set_attr(run_id, "alert_count", len(alert_msgs))

            self.last_run_summary = observability_tracker.end_run(
                run_id,
                status="ok",
                total_deals_found=len(self.all_deals),
                alert_count=len(alert_msgs),
            )

            return {
                "run_id": run_id,
                "run_summary": self.last_run_summary,
                "timestamp": datetime.now().isoformat(),
                "search_params": {
                    "cities": cities,
                    "checkin": checkin,
                    "checkout": checkout,
                    "nights": nights,
                    "group_size": group_size,
                    "pets": pets,
                    "budget_range": f"€{self.budget_min}-{self.budget_max}",
                },
                "validation": validation,
                "total_deals_found": len(self.all_deals),
                "price_alerts": alert_msgs,
                "top_airbnb_deals": self._first_n(airbnb_deals, 15),
                "top_booking_deals": self._first_n(booking_deals, 15),
                "top_10_deals": self._first_n(ranked, 10),
                "summary": summary,
            }

        except Exception as error:
            observability_tracker.event(
                run_id,
                "search_failed",
                error=self._truncate_text(error, 240),
            )
            self.last_run_summary = observability_tracker.end_run(
                run_id,
                status="error",
                error=self._truncate_text(error, 240),
            )
            raise

    def _validate_deals(self, pets: int) -> Dict[str, Any]:
        """Validate and normalize aggregated deals before ranking."""
        raw_deals = list(self.all_deals)
        valid_deals: List[Dict[str, Any]] = []
        reasons: Dict[str, int] = {}

        for deal in raw_deals:
            reason = self._invalid_reason(deal, pets)
            if reason is not None:
                reasons[reason] = reasons.get(reason, 0) + 1
                continue

            normalized = dict(deal)
            price_rounded = self._safe_float(deal.get("price_per_night"))
            normalized["price_per_night"] = float(f"{price_rounded:.2f}")
            normalized["rating"] = min(5.0, max(0.0, self._safe_float(deal.get("rating"), default=0.0)))
            normalized["reviews"] = max(0, self._safe_int(deal.get("reviews"), default=0))
            normalized["currency"] = str(deal.get("currency", "EUR")).upper()

            valid_deals.append(normalized)

        self.all_deals = valid_deals

        return {
            "total_raw": len(raw_deals),
            "valid_count": len(valid_deals),
            "rejected_count": len(raw_deals) - len(valid_deals),
            "rejected_reasons": reasons,
        }

    def _invalid_reason(self, deal: Any, pets: int) -> Optional[str]:
        """Return a rejection reason key if deal is invalid, otherwise None."""
        if not isinstance(deal, dict):
            return "invalid_payload"

        if not str(deal.get("name", "")).strip():
            return "missing_name"
        if not str(deal.get("location", "")).strip():
            return "missing_location"
        if not str(deal.get("source", "")).strip():
            return "missing_source"
        if not str(deal.get("url", "")).strip():
            return "missing_url"

        price = self._safe_float(deal.get("price_per_night"), default=-1.0)
        if price <= 0:
            return "invalid_price"
        if price > float(self.budget_max):
            return "over_budget"

        rating = self._safe_float(deal.get("rating"), default=0.0)
        if rating < 0 or rating > 5:
            return "invalid_rating"

        reviews = self._safe_int(deal.get("reviews"), default=0)
        if reviews < 0:
            return "invalid_reviews"

        if pets > 0 and deal.get("pet_friendly") is not True:
            return "not_pet_friendly"

        return None

    def _safe_float(self, value: Any, default: float = 0.0) -> float:
        try:
            return float(value)
        except (TypeError, ValueError):
            return default

    def _safe_int(self, value: Any, default: int = 0) -> int:
        try:
            return int(float(value))
        except (TypeError, ValueError):
            return default

    def _truncate_text(self, value: Any, limit: int = 160) -> str:
        """Return a safe truncated string without using slice syntax."""
        text = str(value)
        if limit <= 0:
            return ""
        chars: List[str] = []
        idx = 0
        text_len = len(text)
        while idx < text_len and idx < limit:
            chars.append(text[idx])
            idx += 1
        return "".join(chars)

    def _first_n(self, items: List[Dict[str, Any]], count: int) -> List[Dict[str, Any]]:
        """Return first n items without list slicing."""
        if count <= 0:
            return []
        result: List[Dict[str, Any]] = []
        idx = 0
        total = len(items)
        while idx < total and idx < count:
            result.append(items[idx])
            idx += 1
        return result

    async def _search_single_city(
        self,
        city: str,
        checkin: str,
        checkout: str,
        nights: int,
        group_size: int,
        children: int,
        pets: int,
    ) -> List[Dict[str, Any]]:
        """Search all sources for a single city/region."""
        deals: List[Dict[str, Any]] = []

        async def _search_booking() -> List[Dict[str, Any]]:
            started = time.perf_counter()
            try:
                raw_result = await self.booking_scraper.search_booking(
                    city, checkin, checkout, group_size, children
                )
                result: List[Dict[str, Any]] = raw_result if isinstance(raw_result, list) else []
                duration = time.perf_counter() - started
                scraper_metrics.record(
                    source="booking",
                    strategy="smart_chain",
                    success=bool(result),
                    duration=duration,
                    result_count=len(result),
                    error=None if result else "no_results",
                )
                return result
            except Exception as error:
                duration = time.perf_counter() - started
                scraper_metrics.record(
                    source="booking",
                    strategy="smart_chain",
                    success=False,
                    duration=duration,
                    result_count=0,
                    error=str(error),
                )
                print(f"   Warning: Booking.com search failed for {city}: {error}")
                return []

        async def _search_airbnb() -> List[Dict[str, Any]]:
            started = time.perf_counter()
            try:
                raw_result = await self.airbnb_scraper.search_airbnb(
                    city, checkin, checkout, group_size, children, pets, self.budget_max
                )
                result: List[Dict[str, Any]] = raw_result if isinstance(raw_result, list) else []
                duration = time.perf_counter() - started
                scraper_metrics.record(
                    source="airbnb",
                    strategy="smart_chain",
                    success=bool(result),
                    duration=duration,
                    result_count=len(result),
                    error=None if result else "no_results",
                )
                return result
            except Exception as error:
                duration = time.perf_counter() - started
                scraper_metrics.record(
                    source="airbnb",
                    strategy="smart_chain",
                    success=False,
                    duration=duration,
                    result_count=0,
                    error=str(error),
                )
                print(f"   Warning: Airbnb search failed for {city}: {error}")
                return []

        booking_deals, airbnb_deals = await asyncio.gather(
            _search_booking(),
            _search_airbnb(),
        )

        deals.extend(booking_deals)
        deals.extend(airbnb_deals)

        center_parcs_deals = self._get_center_parcs_data(city)
        deals.extend(center_parcs_deals)

        return deals

    def _get_center_parcs_data(self, city: str) -> List[Dict[str, Any]]:
        """
        TODO: Implement real Center Parcs scraping.
        Returning empty list for now to ensure real scraped data from other sources.
        """
        return []

    async def cleanup(self):
        """Clean up browser sessions."""
        try:
            if hasattr(self.airbnb_scraper, "close"):
                await self.airbnb_scraper.close()
        except Exception:
            pass
        try:
            if hasattr(self.booking_scraper, "close"):
                await self.booking_scraper.close()
        except Exception:
            pass


# Backward compatibility alias
HollandVacationAgent = VacationAgent


async def main():
    """Example usage."""
    agent = VacationAgent(budget_min=40, budget_max=250)

    try:
        results = await agent.find_best_deals(
            cities=["Amsterdam", "Berlin", "Antwerp"],
            checkin="2026-02-15",
            checkout="2026-02-22",
            group_size=4,
            pets=1,
        )

        print("\n" + "=" * 60)
        print("RESULTS")
        print("=" * 60 + "\n")
        print(json.dumps(results, indent=2, ensure_ascii=False))

    finally:
        await agent.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
