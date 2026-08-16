import uuid
import random

from exchange.market_state import MarketState
from traders.action import Action
from exchange.enums import Side, OrderType

class RandomTrader:
    def __init__(self, name, money, shares, orders):
        self.name = name
        self.trader_id = uuid.uuid4()

        self.money = money
        self.shares = shares
        self.orders = orders

        self.activity_rate = random.uniform(0.01, 0.1)

        self.order_ttl = random.randint(30, 300)

        self.next_action_tick = 0
        self.average_wait = random.randint(15, 45)

    def decide_action(self, market_state: MarketState):
        if random.random() > self.activity_rate:
            return None

        if (market_state.best_bid is not None and market_state.best_ask is not None):
            reference_price = (market_state.best_bid + market_state.best_ask) / 2

        elif market_state.last_trade_price is not None:
            reference_price = (market_state.last_trade_price)
        else:
            reference_price = 20

        reference_price += random.gauss(-1, 1)

        reference_price = max(1, int(reference_price))

        roll = random.random()

        if (market_state.best_ask == None):
            return None

        if roll < 0.05:
            if market_state.best_ask is None:
                return None

            quantity = int((self.money * random.uniform(0.2, 0.5)) // reference_price)

            if quantity <= 0:
                return None

            quantity = random.randint(1, int(quantity))

            return Action(Side.BUY, market_state.best_ask, quantity, OrderType.MARKET)
        elif roll < 0.10:
            quantity = int(self.shares * random.uniform(0.2, 0.5))

            if quantity <= 0:
                return None

            price = (market_state.best_bid if market_state.best_bid else market_state.best_ask)

            return Action(Side.SELL, price, quantity, OrderType.MARKET)
        elif roll < 0.55:
            price = max(1, reference_price - random.randint(1,3))

            quantity = int((self.money * random.uniform(0.2, 0.5)) // market_state.best_ask)

            if quantity <= 0:
                return None

            quantity = random.randint(1, int(quantity))

            return Action(Side.BUY, price, quantity, OrderType.LIMIT)
        else:
            price = (reference_price + random.randint(1,3))

            quantity = int(self.shares * random.uniform(0.2, 0.5))

            if quantity <= 0:
                return None

            return Action(Side.SELL, price, quantity, OrderType.LIMIT)