import random


class Economy:
    def __init__(self, risk_free_rate=0.05):
        self.risk_free_rate = risk_free_rate
        self.base_rate = risk_free_rate
        self.risk_on = 0.0
        self.flow_multiplier = 1.0

    def apply_rate_shock(self, magnitude):
        self.risk_free_rate = max(0.0, min(0.12, self.risk_free_rate + magnitude * 0.15))
        self.risk_free_rate += 0.05 * (self.base_rate - self.risk_free_rate)

    def update_flow_regime(self):
        self.risk_on += random.gauss(0, 0.05)
        self.risk_on = max(-1.0, min(1.0, self.risk_on))
        self.flow_multiplier = max(0.4, min(1.8, 1.0 + 0.4 * self.risk_on))
