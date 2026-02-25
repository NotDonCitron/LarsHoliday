"""
Deal Ranking System for Holland Vacation Agent
Scores and ranks vacation deals based on multiple criteria
"""

from typing import Any, Dict, List
from dataclasses import dataclass


@dataclass
class Deal:
    """Structured deal data"""
    source: str
    name: str
    price_per_night: float
    rating: float
    reviews: int
    is_dog_friendly: bool
    location: str
    url: str = ""


class DealRanker:
    """
    Ranks vacation deals using a multi-factor scoring system

    Scoring Algorithm:
    - Price score: 0-40 points (max(0, 40 - price/3))
    - Rating score: 0-30 points (rating * 6)
    - Review count: 0-20 points (min(20, reviews/20))
    - Dog-friendly multiplier: 1.4x
    - Weather bonus: 1.2x (if avg temp > 15°C)
    """

    def __init__(self, budget_max: int = 250):
        self.budget_max = budget_max
        self.fx_rates_to_eur = {
            "EUR": 1.0,
            "USD": 0.92,
            "GBP": 1.17,
            "CHF": 1.03,
            "NOK": 0.085,
            "SEK": 0.088,
            "DKK": 0.134,
        }

    def rank_deals(self, deals: List[Dict], nights: int = 7) -> List[Dict]:
        """
        Score and rank all deals

        Args:
            deals: List of deal dictionaries
            nights: Number of nights for the stay

        Returns:
            Sorted list of deals with scores and recommendations
        """
        scored_deals = []

        for deal in deals:
            if not deal or not deal.get("name"):
                continue

            # Calculate base score
            normalized_price = self._normalize_price_to_eur(
                price=deal.get("price_per_night", 0),
                currency=deal.get("currency", "EUR"),
                custom_rate=deal.get("fx_rate_to_eur"),
            )

            deal_for_score = dict(deal)
            deal_for_score["price_per_night"] = normalized_price

            # Calculate base score
            score = self._calculate_base_score(deal_for_score)

            # Apply multipliers
            score = self._apply_multipliers(score, deal_for_score)

            # Calculate total cost (normalized to EUR)
            total_cost = normalized_price * nights

            # Build scored deal
            scored_deal = {
                "rank_score": self._round_to(score, 1),
                "name": deal.get("name", "Unknown"),
                "location": deal.get("location", "Unknown"),
                "price_per_night": self._round_to(normalized_price, 2),
                "total_cost_for_trip": self._round_to(total_cost, 2),
                "rating": deal.get("rating", 0),
                "reviews": deal.get("reviews", 0),
                "pet_friendly": deal.get("pet_friendly", False),
                "source": deal.get("source", "unknown"),
                "url": deal.get("url", ""),
                "image_url": deal.get("image_url", ""),
                "images": deal.get("images", []),
                "weather_forecast": deal.get("weather_forecast"),
                "currency": "EUR",
                "original_currency": str(deal.get("currency", "EUR")).upper(),
                "original_price_per_night": deal.get("price_per_night", 0),
                "recommendation": self._get_recommendation(score, total_cost)
            }

            scored_deals.append(scored_deal)

        # Sort by score descending
        return sorted(scored_deals, key=lambda x: x["rank_score"], reverse=True)

    def _calculate_base_score(self, deal: Dict) -> float:
        """Calculate base score from price, rating, and reviews."""
        score = 0.0

        # 1. Price Score (0-40 points)
        # Lower price = higher score
        price = self._safe_float(deal.get("price_per_night", 0))
        if price <= 0:
            return 0.0  # Invalid deal
        price_score = 40.0 - (price / 3.0)
        if price_score < 0:
            price_score = 0.0
        score += price_score

        # 2. Rating Score (0-30 points)
        # Max 30 points for 5-star rating
        rating = self._safe_float(deal.get("rating", 0))
        rating_score = rating * 6
        score += rating_score

        # 3. Review Count Score (0-20 points)
        # More reviews = more trustworthy
        reviews = self._safe_float(deal.get("reviews", 0))
        review_score = reviews / 20.0
        if review_score > 20.0:
            review_score = 20.0
        score += review_score

        return score

    def _apply_multipliers(self, score: float, deal: Dict) -> float:
        """Apply bonus multipliers to the score"""

        # Dog-friendly multiplier (1.4x)
        if deal.get("pet_friendly", False):
            score *= 1.4

        # Weather bonus (1.2x if good weather)
        weather_bonus = deal.get("weather_bonus", 1.0)
        score *= weather_bonus

        return score

    def _normalize_price_to_eur(self, price: object, currency: object, custom_rate: object = None) -> float:
        """Normalize arbitrary currency to EUR for fair ranking and sorting."""
        base_price = self._safe_float(price)
        if base_price <= 0:
            return 0.0

        if isinstance(custom_rate, (int, float)) and float(custom_rate) > 0:
            return base_price * float(custom_rate)

        code = str(currency or "EUR").upper()
        rate = self.fx_rates_to_eur.get(code, 1.0)
        return base_price * rate

    def _safe_float(self, value: Any, default: float = 0.0) -> float:
        if isinstance(value, bool):
            return default
        if isinstance(value, (int, float)):
            return float(value)
        if isinstance(value, str):
            try:
                return float(value)
            except ValueError:
                return default
        return default

    def _round_to(self, value: float, digits: int = 2) -> float:
        try:
            return float(f"{float(value):.{digits}f}")
        except (TypeError, ValueError):
            return 0.0

    def _first_n(self, items: List[Dict], count: int) -> List[Dict]:
        if count <= 0:
            return []
        out: List[Dict] = []
        idx = 0
        total = len(items)
        while idx < total and idx < count:
            out.append(items[idx])
            idx += 1
        return out

    def _get_recommendation(self, score: float, total_cost: float) -> str:
        """Generate human-readable recommendation"""

        if score > 80:
            tier = "EXCELLENT"
            emoji = "🔥"
        elif score > 60:
            tier = "VERY GOOD"
            emoji = "✅"
        elif score > 40:
            tier = "GOOD"
            emoji = "👍"
        else:
            tier = "BUDGET"
            emoji = "⚠️"

        return f"{emoji} {tier} | €{total_cost:,.0f} total"

    def generate_summary(self, ranked_deals: List[Dict], nights: int) -> Dict:
        """
        Generate summary statistics for the search results

        Args:
            ranked_deals: List of ranked deals
            nights: Number of nights

        Returns:
            Summary dictionary with key insights
        """
        if not ranked_deals:
            return {"status": "No deals found"}

        top_3 = self._first_n(ranked_deals, 3)

        # Calculate budget breakdown
        prices = [d["price_per_night"] for d in ranked_deals]
        budget_breakdown = {
            "nights": nights,
            "cheapest_per_night": min(prices),
            "most_expensive_per_night": max(prices),
            "average_per_night": self._round_to(sum(prices) / len(prices), 2)
        }

        # Find best options
        dog_friendly_count = len([d for d in ranked_deals if d["pet_friendly"]])
        top_rated = max(ranked_deals, key=lambda x: x["rating"])
        cheapest = min(ranked_deals, key=lambda x: x["price_per_night"])

        return {
            "best_overall": top_3[0]["name"] if top_3 else None,
            "budget_overview": budget_breakdown,
            "dog_friendly_options": dog_friendly_count,
            "top_rated_property": top_rated["name"],
            "cheapest_option": cheapest["name"],
            "total_options_found": len(ranked_deals),
            "top_3_recommendations": [
                {
                    "name": d["name"],
                    "score": d["rank_score"],
                    "total_cost": d["total_cost_for_trip"]
                }
                for d in top_3
            ]
        }
