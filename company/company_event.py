import random

class CompanyEvent:
    def __init__(self, money, debt, revenue):
        self.money = money
        self.debt = debt
        self.revenue = revenue
        self.money_effect = random.uniform(0.5, 1.5)
        self.debt_effect = random.uniform(0.5, 2)
        self.revenue_effect = random.uniform(0.25, 1.5)

    def event(self):
        prob = random.random()

        if 0 < prob < 0.1:
            return self.money, self.debt, self.revenue
        elif 0.11 < prob < 0.2:
            return self.money, self.debt, self.revenue
        elif 0.21 < prob < 0.3:
            self.revenue *= self.revenue_effect
            return self.money, self.debt, self.revenue
        else:
            return self.money, self.debt, self.revenue       
