import random
from company.news_event import MarketEvent

LIQUIDITY_TEMPLATES = [
    ("liquidity_dryup", 0.03, 0.08, "Market liquidity thinned; dealers stepped back"),
    ("liquidity_flood", -0.06, -0.02, "Liquidity improved as risk appetite returned"),
]


def generate_liquidity_event(tick):
    kind, lo, hi, headline = random.choice(LIQUIDITY_TEMPLATES)
    magnitude = random.uniform(lo, hi)
    return MarketEvent(
        tick=tick,
        kind=kind,
        magnitude=magnitude,
        headline=headline,
        source="liquidity",
        symbol=None,
    )


def stress_multiplier_from_event(event):
    if event.kind == "liquidity_dryup":
        return 1.0 + abs(event.magnitude) * 8.0
    return max(0.6, 1.0 - abs(event.magnitude) * 4.0)


def duration_from_event(event):
    return random.randint(20, 60)
