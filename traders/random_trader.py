import uuid
import random

from exchange.market_state import MarketState
from traders.action import Action
from exchange.enums import Side, OrderType
from exchange.ticks import DEFAULT_TICK_SIZE, round_to_tick


class RandomTrader:
    def __init__(self, name, money, shares, orders):
        self.name = name
        self.trader_id = uuid.uuid4()

        self.money = money
        self.shares = shares
        self.orders = orders

        self.activity_rate = random.uniform(0.01, 0.1)

        self.order_ttl = random.randint(30, 120)
        self.next_action_tick = 0
        self.average_wait = random.randint(5, 30)
        self.symbol = None
        self.tick_size = DEFAULT_TICK_SIZE
        # Limit offset: 5–30 bps from reference
        self.offset_bps_lo = 5
        self.offset_bps_hi = 30

    def _offset_price(self, reference, side_sign):
        bps = random.uniform(self.offset_bps_lo, self.offset_bps_hi)
        delta = reference * (bps / 10000.0)
        ticks = max(1, int(round(delta / self.tick_size)))
        price = reference + side_sign * ticks * self.tick_size
        return round_to_tick(max(self.tick_size, price), self.tick_size)

    def decide_action(self, market_state: MarketState):
        if random.random() > self.activity_rate:
            return None

        if market_state.best_bid is not None and market_state.best_ask is not None:
            reference_price = (market_state.best_bid + market_state.best_ask) / 2
        elif market_state.last_trade_price is not None:
            reference_price = market_state.last_trade_price
        else:
            reference_price = market_state.fundamental_price or 20

        # Small noise (~±10 bps)
        reference_price *= 1.0 + random.gauss(0, 0.001)
        reference_price = max(self.tick_size, reference_price)

        roll = random.random()

        if roll < 0.05:
            if market_state.best_ask is None:
                return None

            quantity = int((self.money * random.uniform(0.2, 0.5)) // market_state.best_ask)
            if quantity <= 0:
                return None

            quantity = random.randint(1, int(quantity))
            return Action(Side.BUY, market_state.best_ask, quantity, OrderType.MARKET)

        if roll < 0.10:
            if market_state.best_bid is None:
                return None

            quantity = int(self.shares * random.uniform(0.2, 0.5))
            if quantity <= 0:
                return None

            return Action(Side.SELL, market_state.best_bid, quantity, OrderType.MARKET)

        if roll < 0.55:
            if market_state.best_ask is None and self.money <= 0:
                return None

            price = self._offset_price(reference_price, -1)
            quote = market_state.best_ask if market_state.best_ask is not None else reference_price
            quantity = int((self.money * random.uniform(0.2, 0.5)) // quote)
            if quantity <= 0:
                return None

            quantity = random.randint(1, int(quantity))
            return Action(Side.BUY, price, quantity, OrderType.LIMIT)

        quantity = int(self.shares * random.uniform(0.2, 0.5))
        if quantity <= 0:
            return None

        price = self._offset_price(reference_price, +1)
        return Action(Side.SELL, price, quantity, OrderType.LIMIT)
