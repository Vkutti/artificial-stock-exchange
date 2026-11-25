import uuid
import random

from exchange.market_state import MarketState
from traders.action import Action
from exchange.enums import Side, OrderType


class SentimentTrader:
    def __init__(self, name, money, shares, orders):
        self.name = name
        self.trader_id = uuid.uuid4()

        self.money = money
        self.shares = shares
        self.orders = orders

        self.activity_rate = random.uniform(0.02, 0.08)
        self.order_ttl = random.randint(30, 120)
        self.average_wait = random.randint(10, 30)
        self.signal_threshold = random.uniform(0.08, 0.18)
        self.symbol = None

    def decide_action(self, market_state: MarketState):
        if random.random() > self.activity_rate:
            return None

        history = market_state.company.sentiment.history

        if len(history) < 50:
            signal = 0.0
        else:
            short_term = history[-5:]
            long_term = history[-50:]
            short_avg = sum(short_term) / len(short_term)
            long_avg = sum(long_term) / len(long_term)
            signal = 0.7 * short_avg + 0.3 * long_avg

        for event in market_state.recent_events:
            if market_state.current_tick - event.tick <= 120:
                signal += event.magnitude * 0.25

        if abs(signal) < self.signal_threshold:
            return None

        if signal < 0:
            if market_state.best_bid is None or self.shares <= 0:
                return None

            max_quantity = int(self.shares * random.uniform(0.05, 0.2))
            if max_quantity <= 0:
                return None

            return Action(Side.SELL, market_state.best_bid, max_quantity, OrderType.MARKET)

        if market_state.best_ask is None:
            return None

        max_affordable = int((random.uniform(0.05, 0.2) * self.money) // market_state.best_ask)
        if max_affordable <= 0:
            return None

        max_quantity = random.randint(1, max_affordable)
        return Action(Side.BUY, market_state.best_ask, max_quantity, OrderType.MARKET)
