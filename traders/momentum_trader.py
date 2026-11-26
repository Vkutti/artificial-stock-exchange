import uuid
import random

from exchange.market_state import MarketState
from traders.action import Action
from exchange.enums import Side, OrderType


class MomentumTrader:

    def __init__(self, name, money, shares, orders):

        self.name = name
        self.trader_id = uuid.uuid4()

        self.money = money
        self.shares = shares
        self.orders = orders

        self.activity_rate = random.uniform(0.05, 0.2)

        self.order_ttl = random.randint(30, 120)
        # Signal threshold in bps of price vs 20-bar MA
        self.threshold_bps = random.uniform(30, 100)
        self.next_action_tick = 0
        self.average_wait = random.randint(5, 20)
        self.symbol = None

    def decide_action(self, market_state: MarketState):

        if random.random() > self.activity_rate:
            return None

        if market_state.best_bid is not None and market_state.best_ask is not None:
            current_price = (market_state.best_bid + market_state.best_ask) / 2
        elif market_state.last_trade_price is not None:
            current_price = market_state.last_trade_price
        else:
            current_price = market_state.fundamental_price or 20

        if len(market_state.recent_prices) < 20:
            return None

        moving_average = sum(market_state.recent_prices[-20:]) / 20
        if moving_average <= 0:
            return None

        signal_bps = (current_price - moving_average) / moving_average * 10000.0

        if signal_bps >= self.threshold_bps:
            if market_state.best_ask is None:
                return None

            quantity = int((self.money * random.uniform(0.2, 0.5)) // market_state.best_ask)
            if quantity <= 0:
                return None

            return Action(Side.BUY, market_state.best_ask, quantity, OrderType.MARKET)

        if signal_bps <= -self.threshold_bps:
            if market_state.best_bid is None:
                return None

            quantity = int(self.shares * random.uniform(0.2, 0.5))
            if quantity <= 0:
                return None

            return Action(Side.SELL, market_state.best_bid, quantity, OrderType.MARKET)

        return None
