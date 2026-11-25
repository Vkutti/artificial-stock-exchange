import random
from company.news_event import MarketEvent


SOCIAL_TEMPLATES = [
    ("viral_hype", 0.03, 0.08, "is trending positively on social media"),
    ("viral_panic", -0.08, -0.03, "is facing a viral backlash online"),
    ("influencer_boost", 0.02, 0.06, "got a high-profile influencer endorsement"),
    ("rumor_mill", -0.04, 0.04, "is the subject of unverified online rumors"),
]


def generate_social_event(tick, company_name="the company"):
    kind, lo, hi, phrase = random.choice(SOCIAL_TEMPLATES)
    magnitude = random.uniform(lo, hi)
    headline = f"{company_name} {phrase}"
    return MarketEvent(tick=tick, kind=kind, magnitude=magnitude, headline=headline, source="social")


def apply_social_event(company, event: MarketEvent):
    """Sentiment-only noise — no fundamental multipliers (avoids death spirals)."""
    sensitivity = getattr(company.sector, "sentiment_sensitivity", 1.0)
    company.sentiment.set(company.sentiment.value + event.magnitude * sensitivity * 0.5)

    if abs(event.magnitude) > 0.05:
        company.sentiment.regime = "bullish" if event.magnitude > 0 else "bearish"
        company.sentiment.regime_timer = random.randint(10, 40)
