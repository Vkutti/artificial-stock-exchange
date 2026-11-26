import uuid
import random

from exchange.market_state import MarketState
from traders.action import Action
from exchange.enums import Side, OrderType


class FairValueTrader:
    def __init__(self, name, money, shares, orders):
        self.name = name
        self.trader_id = uuid.uuid4()

        self.money = money
        self.shares = shares
        self.orders = orders

        self.activity_rate = random.uniform(0.05, 0.25)

        self.order_ttl = random.randint(30, 120)
        # Belief offset and entry gap in bps of fundamental
        self.fair_value_offset_bps = random.gauss(0, 50)
        self.threshold_bps = random.uniform(50, 150)
        self.next_action_tick = 0
        self.average_wait = random.randint(5, 20)
        self.symbol = None

    def decide_action(self, market_state: MarketState):
        if random.random() > self.activity_rate:
            return None

        fv = market_state.fundamental_price or 20
        fair_value = fv * (1.0 + self.fair_value_offset_bps / 10000.0)
        threshold = abs(fv) * (self.threshold_bps / 10000.0)

        if market_state.best_bid is not None and market_state.best_ask is not None:
            current_price = (market_state.best_bid + market_state.best_ask) / 2
        elif market_state.last_trade_price is not None:
            current_price = market_state.last_trade_price
        else:
            current_price = fv

        if current_price <= fair_value - threshold:
            if market_state.best_ask is None:
                return None

            quantity = int((self.money * random.uniform(0.2, 0.5)) // market_state.best_ask)

            if quantity <= 0:
                return None

            return Action(Side.BUY, market_state.best_ask, quantity, OrderType.MARKET)

        if current_price >= fair_value + threshold:
            if market_state.best_bid is None:
                return None

            quantity = int(self.shares * random.uniform(0.2, 0.5))

            if quantity <= 0:
                return None

            return Action(Side.SELL, market_state.best_bid, quantity, OrderType.MARKET)

        return None
