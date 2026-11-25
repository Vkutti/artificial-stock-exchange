import random
from dataclasses import dataclass, field
from itertools import count

_event_ids = count(1)


@dataclass
class MarketEvent:
    tick: int
    kind: str
    magnitude: float
    headline: str
    source: str = "news"
    event_id: int = field(default_factory=lambda: next(_event_ids))


# Symmetric bull/bear set; magnitudes kept small so multi-day compounding stays stable
NEWS_TEMPLATES = [
    ("earnings_beat", 0.02, 0.05, "reported better-than-expected earnings"),
    ("earnings_miss", -0.05, -0.02, "missed earnings expectations"),
    ("product_launch", 0.02, 0.04, "announced a major product launch"),
    ("scandal", -0.05, -0.02, "faces a regulatory investigation"),
    ("acquisition", 0.02, 0.04, "announced an acquisition deal"),
    ("guidance_cut", -0.04, -0.02, "cut forward guidance"),
]


def _clamp_multiplier(magnitude, lo=0.98, hi=1.02):
    """Per-event fundamental multiplier — tight so weeks of news cannot erase the firm."""
    return max(lo, min(hi, 1.0 + magnitude))


def generate_news_event(tick, company_name="the company"):
    kind, lo, hi, phrase = random.choice(NEWS_TEMPLATES)
    magnitude = random.uniform(lo, hi)
    headline = f"{company_name} {phrase}"
    return MarketEvent(tick=tick, kind=kind, magnitude=magnitude, headline=headline, source="news")


def apply_news_event(company, event: MarketEvent):
    """Shock fundamentals and sentiment from a news event (clamped, mild)."""
    before_fv = company.fundamental_value
    impact = _clamp_multiplier(event.magnitude)

    if event.kind in ("earnings_beat", "earnings_miss", "guidance_cut"):
        company.earnings *= impact
        company.revenue *= _clamp_multiplier(event.magnitude * 0.5)
    elif event.kind == "product_launch":
        company.expected_revenue_growth += event.magnitude * 0.01
        company.revenue *= _clamp_multiplier(event.magnitude * 0.25)
    elif event.kind == "scandal":
        company.money *= _clamp_multiplier(event.magnitude * 0.25)
        company.expected_revenue_growth += event.magnitude * 0.02
    elif event.kind == "acquisition":
        company.debt *= _clamp_multiplier(abs(event.magnitude) * 0.2)
        company.revenue *= _clamp_multiplier(event.magnitude * 0.25)

    company.expected_revenue_growth = max(-0.05, min(0.15, company.expected_revenue_growth))
    company.update_fundamental_value()

    # Hard cap: one headline cannot move FV more than ±3%
    if before_fv > 0:
        ratio = company.fundamental_value / before_fv
        if ratio > 1.03:
            company.fundamental_value = before_fv * 1.03
        elif ratio < 0.97:
            company.fundamental_value = before_fv * 0.97

    sentiment_delta = event.magnitude * getattr(
        company.sector, "sentiment_sensitivity", 1.0
    ) * 0.4
    company.sentiment.set(company.sentiment.value + sentiment_delta)

    if event.magnitude > 0.03:
        company.sentiment.regime = "bullish"
        company.sentiment.regime_timer = random.randint(30, 80)
    elif event.magnitude < -0.03:
        company.sentiment.regime = "bearish"
        company.sentiment.regime_timer = random.randint(30, 80)
