import random
from company.news_event import MarketEvent

SECTOR_TEMPLATES = [
    ("sector_boom", 0.02, 0.05, "sector outlook improved on strong demand"),
    ("sector_slump", -0.05, -0.02, "sector faced regulatory and demand pressure"),
    ("sector_innovation", 0.02, 0.04, "sector buzz rose on innovation cycle"),
    ("sector_cost_shock", -0.04, -0.02, "sector costs spiked unexpectedly"),
]


def generate_sector_event(tick, sector_name):
    kind, lo, hi, phrase = random.choice(SECTOR_TEMPLATES)
    magnitude = random.uniform(lo, hi)
    headline = f"{sector_name} {phrase}"
    return MarketEvent(
        tick=tick,
        kind=kind,
        magnitude=magnitude,
        headline=headline,
        source="sector",
        symbol=None,
        sector=sector_name,
    )


def apply_sector_event(company, event):
    before = company.fundamental_value
    impact = max(0.97, min(1.03, 1.0 + event.magnitude * 0.6))
    company.earnings *= impact
    company.expected_revenue_growth += event.magnitude * 0.015
    company.expected_revenue_growth = max(-0.05, min(0.15, company.expected_revenue_growth))
    company.update_fundamental_value()
    if before > 0:
        ratio = company.fundamental_value / before
        if ratio > 1.03:
            company.fundamental_value = before * 1.03
        elif ratio < 0.97:
            company.fundamental_value = before * 0.97
    company.sentiment.set(company.sentiment.value + event.magnitude * 0.35)
