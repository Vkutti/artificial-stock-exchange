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

        self.activity_rate = random.uniform(0.02, 0.08)

        self.order_ttl = random.randint(30, 300)

        self.threshold = random.uniform(1, 3)

        self.next_action_tick = 0
        self.average_wait = random.randint(5, 20)

    def decide_action(self, market_state: MarketState):

        if random.random() > self.activity_rate:
            return None

        if (market_state.best_bid is not None and market_state.best_ask is not None):
            current_price = (market_state.best_bid + market_state.best_ask) / 2
        elif market_state.last_trade_price is not None:
            current_price = market_state.last_trade_price
        else:
            return None
        
        if len(market_state.recent_prices) < 20:
            return None

        moving_average = (sum(market_state.recent_prices[-20:]) / 20)

        signal = (current_price - moving_average)

        if signal > self.threshold:
            if market_state.best_ask is None:
                return None

            max_quantity = self.money // market_state.best_ask

            if max_quantity <= 0:
                return None

            quantity = random.randint(1, int(max_quantity))

            return Action(Side.BUY, market_state.best_ask, quantity, OrderType.MARKET)
        elif signal < -self.threshold:
            if market_state.best_bid is None:
                return None

            max_quantity = self.shares

            if max_quantity <= 0:
                return None

            quantity = random.randint(1, int(max_quantity))

            return Action(Side.SELL, market_state.best_bid, quantity, OrderType.MARKET)

        return None