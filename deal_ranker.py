"""
Deal Ranking System for Holland Vacation Agent
Scores and ranks vacation deals based on multiple criteria
"""

from typing import List, Dict
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
            score = self._calculate_base_score(deal)

            # Apply multipliers
            score = self._apply_multipliers(score, deal)

            # Calculate total cost
            total_cost = deal.get("price_per_night", 0) * nights

            # Build scored deal
            scored_deal = {
                "rank_score": round(score, 1),
                "name": deal.get("name", "Unknown"),
                "location": deal.get("location", "Unknown"),
                "price_per_night": deal.get("price_per_night", 0),
                "total_cost_for_trip": total_cost,
                "rating": deal.get("rating", 0),
                "reviews": deal.get("reviews", 0),
                "pet_friendly": deal.get("pet_friendly", False),
                "source": deal.get("source", "unknown"),
                "url": deal.get("url", ""),
                "weather_forecast": deal.get("weather_forecast"),
                "recommendation": self._get_recommendation(score, total_cost)
            }

            scored_deals.append(scored_deal)

        # Sort by score descending
        return sorted(scored_deals, key=lambda x: x["rank_score"], reverse=True)

    def _calculate_base_score(self, deal: Dict) -> float:
        """Calculate base score from price, rating, and reviews"""
        score = 0.0

        # 1. Price Score (0-40 points)
        # Lower price = higher score
        price = deal.get("price_per_night", 0)
        if price <= 0:
            return 0.0 # Invalid deal
        price_score = max(0, 40 - (price / 3))
        score += price_score

        # 2. Rating Score (0-30 points)
        # Max 30 points for 5-star rating
        rating = deal.get("rating", 0)
        rating_score = rating * 6
        score += rating_score

        # 3. Review Count Score (0-20 points)
        # More reviews = more trustworthy
        reviews = deal.get("reviews", 0)
        review_score = min(20, reviews / 20)
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

        top_3 = ranked_deals[:3]

        # Calculate budget breakdown
        prices = [d["price_per_night"] for d in ranked_deals]
        budget_breakdown = {
            "nights": nights,
            "cheapest_per_night": min(prices),
            "most_expensive_per_night": max(prices),
            "average_per_night": round(sum(prices) / len(prices), 2)
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
