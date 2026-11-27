import uuid
import random

from exchange.market_state import MarketState
from traders.action import Action
from exchange.enums import Side, OrderType


class BreakoutTrader:
    def __init__(self, name, money, shares, orders):
        self.name = name
        self.trader_id = uuid.uuid4()
        self.money = money
        self.shares = shares
        self.orders = orders
        self.activity_rate = random.uniform(0.04, 0.15)
        self.order_ttl = random.randint(15, 60)
        self.average_wait = random.randint(5, 18)
        self.lookback = random.randint(20, 50)
        self.buffer_bps = random.uniform(15, 40)
        self.symbol = None

    def decide_action(self, market_state: MarketState):
        if random.random() > self.activity_rate * market_state.flow_multiplier:
            return None
        prices = market_state.recent_prices
        if len(prices) < self.lookback:
            return None
        if market_state.best_bid is None or market_state.best_ask is None:
            return None

        window = prices[-self.lookback :]
        hi = max(window)
        lo = min(window)
        mid = 0.5 * (market_state.best_bid + market_state.best_ask)
        if hi <= 0:
            return None

        up = hi * (1.0 + self.buffer_bps / 10000.0)
        down = lo * (1.0 - self.buffer_bps / 10000.0)

        if mid >= up:
            qty = int((self.money * random.uniform(0.15, 0.4)) // market_state.best_ask)
            if qty <= 0:
                return None
            return Action(Side.BUY, market_state.best_ask, qty, OrderType.MARKET)

        if mid <= down:
            qty = int(self.shares * random.uniform(0.15, 0.4))
            if qty <= 0:
                return None
            return Action(Side.SELL, market_state.best_bid, qty, OrderType.MARKET)
        return None
