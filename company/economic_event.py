import random
from company.news_event import MarketEvent


# Balanced macro set (equal bull/bear count)
ECONOMIC_TEMPLATES = [
    ("rate_hike", -0.04, -0.02, "Interest rates rose, pressuring valuations"),
    ("rate_cut", 0.02, 0.04, "Interest rates fell, supporting valuations"),
    ("growth_boom", 0.02, 0.05, "Macro growth outlook improved"),
    ("recession_fear", -0.05, -0.02, "Recession fears intensified"),
    ("soft_landing", 0.02, 0.04, "Soft-landing hopes lifted risk assets"),
    ("inflation_spike", -0.04, -0.02, "Inflation unexpectedly spiked"),
]


def apply_economic_event(company, event: MarketEvent):
    """Mild macro shocks to PE and growth; mean-reverting bounds."""
    before_fv = company.fundamental_value

    if event.kind in ("rate_hike", "rate_cut", "inflation_spike"):
        company.pe_ratio = max(10.0, min(35.0, company.pe_ratio * (1.0 + event.magnitude * 0.35)))
    elif event.kind in ("growth_boom", "recession_fear", "soft_landing"):
        company.expected_revenue_growth += event.magnitude * 0.03
        company.expected_revenue_growth = max(-0.05, min(0.12, company.expected_revenue_growth))

    company.update_fundamental_value()

    if before_fv > 0:
        ratio = company.fundamental_value / before_fv
        if ratio > 1.03:
            company.fundamental_value = before_fv * 1.03
        elif ratio < 0.97:
            company.fundamental_value = before_fv * 0.97

    company.sentiment.set(company.sentiment.value + event.magnitude * 0.3)


def generate_economic_event(tick):
    kind, lo, hi, headline = random.choice(ECONOMIC_TEMPLATES)
    magnitude = random.uniform(lo, hi)
    return MarketEvent(tick=tick, kind=kind, magnitude=magnitude, headline=headline, source="economic")
