import os
import sys

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from deal_ranker import DealRanker


def _deal(name: str, price: float, currency: str = "EUR", fx_rate_to_eur=None):
    deal = {
        "name": name,
        "location": "Amsterdam",
        "price_per_night": price,
        "currency": currency,
        "rating": 4.5,
        "reviews": 120,
        "pet_friendly": True,
        "source": "airbnb",
        "url": f"https://example.com/{name.lower().replace(' ', '-')}",
    }
    if fx_rate_to_eur is not None:
        deal["fx_rate_to_eur"] = fx_rate_to_eur
    return deal


def test_ranker_normalizes_known_currency_to_eur():
    ranker = DealRanker(budget_max=400)
    ranked = ranker.rank_deals([_deal("USD Deal", 100, "USD")], nights=2)

    assert len(ranked) == 1
    item = ranked[0]
    assert item["currency"] == "EUR"
    assert item["original_currency"] == "USD"
    assert item["original_price_per_night"] == 100
    assert item["price_per_night"] == 92.0  # 100 * 0.92
    assert item["total_cost_for_trip"] == 184.0


def test_ranker_uses_custom_fx_override_when_provided():
    ranker = DealRanker(budget_max=400)
    ranked = ranker.rank_deals([
        _deal("Custom FX Deal", 100, "USD", fx_rate_to_eur=0.5),
    ], nights=3)

    item = ranked[0]
    assert item["price_per_night"] == 50.0
    assert item["total_cost_for_trip"] == 150.0


def test_ranker_falls_back_to_1_for_unknown_currency():
    ranker = DealRanker(budget_max=400)
    ranked = ranker.rank_deals([_deal("Unknown FX Deal", 100, "XYZ")], nights=1)

    item = ranked[0]
    assert item["price_per_night"] == 100.0
    assert item["total_cost_for_trip"] == 100.0
