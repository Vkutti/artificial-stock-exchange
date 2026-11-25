import random


class CompanyEvent:
    def __init__(self, money, debt, revenue):
        self.money = money
        self.debt = debt
        self.revenue = revenue
        # Mild balance-sheet noise (daily)
        self.money_effect = random.uniform(0.99, 1.01)
        self.debt_effect = random.uniform(0.995, 1.01)
        self.revenue_effect = random.uniform(0.99, 1.01)
        self.triggered = False
        self.kind = None
        self.magnitude = 0.0

    def event(self):
        prob = random.random()

        if prob < 0.1:
            self.money *= self.money_effect
            self.triggered = True
            self.kind = "cash_shock"
            self.magnitude = self.money_effect - 1.0
            return self.money, self.debt, self.revenue
        elif prob < 0.2:
            self.debt *= self.debt_effect
            self.triggered = True
            self.kind = "debt_shock"
            self.magnitude = 1.0 - self.debt_effect
            return self.money, self.debt, self.revenue
        elif prob < 0.3:
            self.revenue *= self.revenue_effect
            self.triggered = True
            self.kind = "revenue_shock"
            self.magnitude = self.revenue_effect - 1.0
            return self.money, self.debt, self.revenue
        else:
            return self.money, self.debt, self.revenue
