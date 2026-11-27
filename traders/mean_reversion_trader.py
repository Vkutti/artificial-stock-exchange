import uuid
import random

from exchange.market_state import MarketState
from traders.action import Action
from exchange.enums import Side, OrderType


class MeanReversionTrader:
    def __init__(self, name, money, shares, orders):
        self.name = name
        self.trader_id = uuid.uuid4()
        self.money = money
        self.shares = shares
        self.orders = orders
        self.activity_rate = random.uniform(0.05, 0.18)
        self.order_ttl = random.randint(20, 90)
        self.average_wait = random.randint(5, 20)
        self.lookback = random.randint(15, 40)
        self.threshold_bps = random.uniform(40, 120)
        self.symbol = None

    def decide_action(self, market_state: MarketState):
        if random.random() > self.activity_rate * market_state.flow_multiplier:
            return None
        prices = market_state.recent_prices
        if len(prices) < self.lookback:
            return None
        if market_state.best_bid is None or market_state.best_ask is None:
            return None

        mid = 0.5 * (market_state.best_bid + market_state.best_ask)
        mean = sum(prices[-self.lookback :]) / self.lookback
        if mean <= 0:
            return None
        gap_bps = (mid - mean) / mean * 10000.0

        if gap_bps >= self.threshold_bps:
            qty = int(self.shares * random.uniform(0.1, 0.35))
            if qty <= 0:
                return None
            return Action(Side.SELL, market_state.best_bid, qty, OrderType.MARKET)

        if gap_bps <= -self.threshold_bps:
            qty = int((self.money * random.uniform(0.1, 0.35)) // market_state.best_ask)
            if qty <= 0:
                return None
            return Action(Side.BUY, market_state.best_ask, qty, OrderType.MARKET)
        return None
