import random

class Sentiment:
    def __init__(self, initial=0.0):
        self.value = initial
        self.history = []

        self.regime = "neutral"
        self.regime_timer = 0

    def update(self):
        if self.regime_timer <= 0:
            roll = random.random()

            if roll < 0.15:
                self.regime = "bearish"
            elif roll < 0.30:
                self.regime = "bullish"
            else:
                self.regime = "neutral"

            self.regime_timer = random.randint(50, 200)

        self.regime_timer -= 1

        if self.regime == "bullish":
            drift = 0.02
        elif self.regime == "bearish":
            drift = -0.02
        else:
            drift = 0.0

        noise = random.gauss(0, 0.03)

        self.value += drift + noise

        self.value = max(-1.0, min(1.0, self.value))

        self.history.append(self.value)

    def set(self, value):
        self.value = max(-1.0, min(1.0, value))
        self.history.append(self.value)