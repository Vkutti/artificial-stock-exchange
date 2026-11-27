import uuid
import random

from exchange.market_state import MarketState
from traders.action import Action
from exchange.enums import Side, OrderType


class AttentionTrader:
    def __init__(self, name, money, shares, orders):
        self.name = name
        self.trader_id = uuid.uuid4()
        self.money = money
        self.shares = shares
        self.orders = orders
        self.activity_rate = random.uniform(0.03, 0.12)
        self.order_ttl = random.randint(10, 45)
        self.average_wait = random.randint(8, 25)
        self.symbol = None
        self._last_volume = 0

    def decide_action(self, market_state: MarketState):
        if random.random() > self.activity_rate * market_state.flow_multiplier:
            return None

        vol_jump = market_state.volume - self._last_volume
        self._last_volume = market_state.volume

        headline_score = 0.0
        for event in market_state.recent_events:
            if market_state.current_tick - event.tick <= 30:
                headline_score += event.sign * event.intensity

        stressed = getattr(market_state, "liquidity_stress", 1.0) > 1.2
        if abs(headline_score) < 0.35 and vol_jump < 40 and not stressed:
            return None

        if market_state.best_bid is None or market_state.best_ask is None:
            return None

        bullish = headline_score > 0 or (headline_score == 0 and vol_jump > 0 and random.random() < 0.55)
        if bullish:
            qty = int((self.money * random.uniform(0.08, 0.3)) // market_state.best_ask)
            if qty <= 0:
                return None
            return Action(Side.BUY, market_state.best_ask, qty, OrderType.MARKET)

        qty = int(self.shares * random.uniform(0.08, 0.3))
        if qty <= 0:
            return None
        return Action(Side.SELL, market_state.best_bid, qty, OrderType.MARKET)
