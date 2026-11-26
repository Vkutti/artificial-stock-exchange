import uuid
import random

from exchange.market_state import MarketState
from traders.action import Action
from exchange.enums import Side, OrderType


class IndexFundTrader:
    """Passive buyer providing steady demand flow."""

    def __init__(self, name, money, shares, orders):
        self.name = name
        self.trader_id = uuid.uuid4()

        self.money = money
        self.shares = shares
        self.orders = orders

        self.activity_rate = random.uniform(0.005, 0.02)
        self.order_ttl = random.randint(30, 120)
        self.average_wait = random.randint(30, 90)
        self.symbol = None

    def decide_action(self, market_state: MarketState):
        flow = getattr(market_state, "flow_multiplier", 1.0)
        if random.random() > self.activity_rate * flow:
            return None

        if market_state.best_ask is None:
            return None

        if market_state.best_bid is not None and market_state.best_ask is not None:
            current_price = (market_state.best_bid + market_state.best_ask) / 2
        elif market_state.last_trade_price is not None:
            current_price = market_state.last_trade_price
        else:
            current_price = market_state.best_ask

        fraction = random.uniform(0.02, 0.05) * max(0.5, flow)
        quantity = int((fraction * self.money) // current_price)
        if quantity <= 0:
            return None

        return Action(Side.BUY, market_state.best_ask, quantity, OrderType.MARKET)
