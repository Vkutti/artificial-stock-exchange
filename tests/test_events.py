from company.company import Company
from company.company_event import CompanyEvent
from company.news_event import generate_news_event, apply_news_event, NEWS_TEMPLATES
from company.social_event import generate_social_event, apply_social_event
from company.economic_event import generate_economic_event, apply_economic_event, ECONOMIC_TEMPLATES
from company.sector import Sector
from simulation.clock import MINUTES_PER_DAY
import random


def test_company_event_probability_bands_cover_unit_interval():
    hits = {"cash_shock": 0, "debt_shock": 0, "revenue_shock": 0, "none": 0}

    for _ in range(1000):
        event = CompanyEvent(100, 50, 200)
        event.event()
        if event.triggered:
            hits[event.kind] += 1
        else:
            hits["none"] += 1

    assert hits["cash_shock"] > 0
    assert hits["debt_shock"] > 0
    assert hits["revenue_shock"] > 0
    assert hits["none"] > 500


def test_news_templates_are_sign_balanced():
    bull = sum(1 for t in NEWS_TEMPLATES if t[1] > 0)
    bear = sum(1 for t in NEWS_TEMPLATES if t[2] < 0)
    assert bull == bear


def test_economic_templates_are_sign_balanced():
    bull = sum(1 for t in ECONOMIC_TEMPLATES if t[1] > 0)
    bear = sum(1 for t in ECONOMIC_TEMPLATES if t[2] < 0)
    assert bull == bear


def test_news_event_moves_sentiment_and_fundamentals():
    company = Company("ABC", "Technology", 1e6, 1e5, 1e5, 5e5, 2e6, 1e6, 0.2)
    event = generate_news_event(10, company.name)
    before = company.fundamental_value
    apply_news_event(company, event)

    assert company.fundamental_value > 0
    assert abs(event.magnitude) <= 0.05
    assert company.fundamental_value <= before * 1.03001
    assert company.fundamental_value >= before * 0.96999


def test_social_does_not_change_fundamentals():
    company = Company("ABC", "Finance", 1e6, 1e5, 1e5, 5e5, 2e6, 1e6, 0.2)
    before_fv = company.fundamental_value
    before_rev = company.revenue
    social = generate_social_event(20, company.name)
    apply_social_event(company, social)
    assert social.source == "social"
    assert company.fundamental_value == before_fv
    assert company.revenue == before_rev


def test_social_and_economic_events_apply():
    company = Company("ABC", "Finance", 1e6, 1e5, 1e5, 5e5, 2e6, 1e6, 0.2)

    social = generate_social_event(20, company.name)
    apply_social_event(company, social)
    assert len(company.sentiment.history) >= 1

    economic = generate_economic_event(30)
    apply_economic_event(company, economic)
    assert economic.source == "economic"
    assert company.fundamental_value > 0


def test_sector_multipliers():
    tech = Sector("Technology")
    assert tech.growth_multiplier > 1.0
    assert tech.sentiment_sensitivity > 1.0

    unknown = Sector("UnknownSector")
    assert unknown.growth_multiplier == 1.0


def test_many_news_events_cannot_crush_fundamental_below_half():
    random.seed(42)
    company = Company(
        "ABC Incorporated",
        "Technology",
        10000000,
        2000000,
        1000000,
        3600000,
        8000000,
        1000000,
        0.5,
    )
    start_fv = company.fundamental_value

    for t in range(0, 100):
        event = generate_news_event(t, company.name)
        apply_news_event(company, event)

    assert company.fundamental_value >= start_fv * 0.5


def test_21_day_event_path_not_systematically_crushed():
    """With calibrated events + daily updates, most 21d paths stay within a wide band."""
    rets = []
    for seed in range(25):
        random.seed(seed)
        company = Company(
            "ABC Incorporated",
            "Technology",
            10000000,
            2000000,
            1000000,
            3600000,
            8000000,
            1000000,
            0.5,
            symbol="ABC",
        )
        start = company.fundamental_value
        for day in range(21):
            for _ in range(MINUTES_PER_DAY // 15):
                company.sentiment.update()
            apply_news_event(company, generate_news_event(day * MINUTES_PER_DAY, company.name))
            apply_social_event(company, generate_social_event(day * MINUTES_PER_DAY, company.name))
            if day % 5 == 0:
                apply_economic_event(company, generate_economic_event(day * MINUTES_PER_DAY))
            company.update()
        rets.append(company.fundamental_value / start - 1)

    mean_ret = sum(rets) / len(rets)
    frac_crushed = sum(1 for r in rets if r < -0.40) / len(rets)
    assert mean_ret > -0.20
    assert frac_crushed < 0.25
