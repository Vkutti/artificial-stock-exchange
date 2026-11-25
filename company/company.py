import random
from company.sentiment import Sentiment
from company.company_event import CompanyEvent
from company.sector import Sector


class Company:
    def __init__(self, name, industry, money, debt, earnings, revenue, book_value, total_shares, dividend, symbol=None):
        self.name = name
        self.symbol = symbol or "".join(ch for ch in name.upper() if ch.isalnum())[:4] or "TICK"
        self.industry = industry
        self.sector = Sector(industry)

        self.money = money
        self.debt = debt

        self.revenue = revenue
        self.earnings = earnings
        self.book_value = book_value

        self.total_shares = total_shares
        self.shares_outstanding = total_shares

        self.dividend = dividend

        self.expected_revenue_growth = 0.05

        self.revenue_volatility = 0.02

        self.margin_volatility = 0.01

        self.pe_ratio = 20

        self.book_value_per_share = (self.book_value / max(self.shares_outstanding, 1))

        self.earnings_per_share = (self.earnings / max(self.shares_outstanding, 1))

        self.fundamental_value = 0

        self.market_cap = 0
        self.price_to_earnings = 0
        self.price_to_book = 0

        self.market_price = None

        self.sentiment = Sentiment()

        self.sector.apply_to_company(self)

        # Baselines after sector scaling — used for mild mean reversion
        self.base_pe_ratio = self.pe_ratio
        self.base_expected_revenue_growth = self.expected_revenue_growth
        self.base_revenue_volatility = self.revenue_volatility

        self.update_fundamental_value()

        self.last_internal_event = None

    def update_fundamental_value(self):
        self.earnings_per_share = (self.earnings / max(self.shares_outstanding, 1))

        self.book_value_per_share = (self.book_value / max(self.shares_outstanding, 1))

        earnings_value = (self.earnings_per_share * self.pe_ratio)

        self.fundamental_value = max(earnings_value, 0.01)

    def update(self):
        """One trading-day fundamental step (not a full annual period)."""
        company_event = CompanyEvent(self.money, self.debt, self.revenue)
        self.money, self.debt, self.revenue = company_event.event()

        if company_event.triggered:
            self.last_internal_event = company_event
            self.sentiment.set(self.sentiment.value + company_event.magnitude * 0.2)
        else:
            self.last_internal_event = None

        # Annualized growth/vol → daily trading-day increments
        daily_mean = self.expected_revenue_growth / 252.0
        daily_vol = self.revenue_volatility / (252.0 ** 0.5)
        revenue_growth = random.gauss(daily_mean, daily_vol)
        revenue_growth = max(-0.015, min(0.015, revenue_growth))

        self.revenue *= (1 + revenue_growth)

        current_margin = (self.earnings / max(self.revenue, 1))
        margin_change = random.gauss(0, self.margin_volatility / (252.0 ** 0.5))
        earnings_margin = max(0.01, min(0.50, current_margin + margin_change))
        self.earnings = self.revenue * earnings_margin

        retained_earnings = self.earnings * 0.70
        dividend_payout = self.earnings * self.dividend * 0.30
        self.money += retained_earnings - dividend_payout

        interest_expense = self.debt * (0.05 / 252.0)
        self.money -= interest_expense

        self.book_value += retained_earnings - interest_expense - dividend_payout
        self.book_value = max(self.book_value, 0)

        # Pull PE / growth / vol gently back toward baselines (stops event death spirals)
        self.pe_ratio += 0.15 * (self.base_pe_ratio - self.pe_ratio)
        self.expected_revenue_growth += 0.15 * (
            self.base_expected_revenue_growth - self.expected_revenue_growth
        )
        self.revenue_volatility += 0.15 * (
            self.base_revenue_volatility - self.revenue_volatility
        )

        self.update_fundamental_value()


    def update_market_stats(self, market_price):
        if market_price is None:
            return

        self.market_price = market_price

        self.market_cap = (market_price * self.shares_outstanding)

        eps = (self.earnings / max(self.shares_outstanding, 1))

        bvps = (self.book_value / max(self.shares_outstanding, 1))

        self.price_to_earnings = (market_price / max(eps, 0.000001))

        self.price_to_book = (market_price / max(bvps, 0.000001))

    def __str__(self):
        return (
            f"Company: "
            f"{self.name}, "
            f"{self.money}, "
            f"{self.debt}, "
            f"{self.revenue}, "
            f"{self.earnings}, "
            f"{self.book_value},"
            f"{self.fundamental_value},"
            f"{self.market_price}"
        )

    def __repr__(self):
        return (
            f"Company: "
            f"{self.name}, "
            f"{self.money}, "
            f"{self.debt}, "
            f"{self.revenue}, "
            f"{self.earnings}, "
            f"{self.book_value},"
            f"{self.fundamental_value},"
            f"{self.market_price}"
        )
