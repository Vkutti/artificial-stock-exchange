import random

class Company:
    def __init__(self, name, industry, money, debt, earnings, revenue, book_value, total_shares, dividend):
        self.name = name
        self.industry = industry

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

        self.update_fundamental_value()

    def update_fundamental_value(self):
        self.earnings_per_share = (self.earnings / max(self.shares_outstanding, 1))

        self.book_value_per_share = (self.book_value / max(self.shares_outstanding, 1))

        earnings_value = (self.earnings_per_share * self.pe_ratio)

        self.fundamental_value = max(earnings_value, 0.01)

    def update(self):
        revenue_growth = random.gauss(self.expected_revenue_growth, self.revenue_volatility)

        revenue_growth = max(-0.20, min(0.20, revenue_growth))

        self.revenue *= (1 + revenue_growth)

        current_margin = (self.earnings / max(self.revenue, 1))

        margin_change = random.gauss(0, self.margin_volatility)

        earnings_margin = (current_margin + margin_change)

        earnings_margin = max(0.01, min(0.50, earnings_margin))

        self.earnings = (self.revenue * earnings_margin)

        retained_earnings = (self.earnings * 0.70)

        self.money += retained_earnings

        interest_rate = 0.05

        interest_expense = (self.debt * interest_rate)

        self.money -= interest_expense

        self.book_value += (retained_earnings - interest_expense)

        self.book_value = max(self.book_value, 0)

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