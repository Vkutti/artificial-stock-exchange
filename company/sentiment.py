class Sentiment:
    def __init__(self, initial=0.0):
        self.value = initial
        self.history = []

    def update(self, change):
        self.value += change
        self.value = max(-1.0, min(1.0, self.value))
        self.history.append(self.value)

    def set(self, value):
        self.value = max(-1.0, min(1.0, value))
        self.history.append(self.value)