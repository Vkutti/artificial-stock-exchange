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

        self.order_ttl = random.randint(30, 300)

        self.fair_value_offset = random.gauss(0, 5)

        self.threshold = random.uniform(1, 3)

        self.next_action_tick = 0
        self.average_wait = random.randint(5, 20)

    def decide_action(self, market_state: MarketState):
        if random.random() > self.activity_rate:
            return None
        
        fair_value = (market_state.fundamental_price + self.fair_value_offset)

        if (market_state.best_bid is not None and market_state.best_ask is not None):
            current_price = (market_state.best_bid + market_state.best_ask) / 2
        elif market_state.last_trade_price is not None:
            current_price = (market_state.last_trade_price)
        else:
            current_price = 20

        if current_price <= fair_value - self.threshold:
            if market_state.best_ask is None:
                return None

            quantity = int((self.money * random.uniform(0.2, 0.5)) // current_price)

            if quantity <= 0:
                return None

            return Action(Side.BUY, market_state.best_ask, quantity, OrderType.MARKET)
        elif current_price >= fair_value + self.threshold:
            if market_state.best_bid is None:
                return None
            
            quantity = int(self.shares * random.uniform(0.2, 0.5))

            if quantity <= 0:
                return None

            return Action(Side.SELL, market_state.best_bid, quantity, OrderType.MARKET)

        return None