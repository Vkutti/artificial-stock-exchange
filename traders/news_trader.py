import uuid
import random

from exchange.market_state import MarketState
from traders.action import Action
from exchange.enums import Side, OrderType


class NewsTrader:
    def __init__(self, name, money, shares, orders):
        self.name = name
        self.trader_id = uuid.uuid4()

        self.money = money
        self.shares = shares
        self.orders = orders

        self.activity_rate = random.uniform(0.08, 0.2)
        self.order_ttl = random.randint(15, 90)
        self.average_wait = random.randint(8, 25)
        self.symbol = None

        self.reaction_window = 60
        self.min_intensity = 0.4
        self.reacted_event_ids = set()

    def decide_action(self, market_state: MarketState):
        if random.random() > self.activity_rate * market_state.flow_multiplier:
            return None

        relevant = []
        for event in market_state.recent_events:
            if event.source not in ("news", "economic"):
                continue
            if market_state.current_tick - event.tick > self.reaction_window:
                continue
            if event.intensity < self.min_intensity:
                continue
            eid = (event.tick, event.kind, event.headline)
            if eid in self.reacted_event_ids:
                continue
            relevant.append(event)

        if not relevant:
            return None

        event = max(
            relevant,
            key=lambda e: e.intensity / (1 + market_state.current_tick - e.tick),
        )
        self.reacted_event_ids.add((event.tick, event.kind, event.headline))

        intensity = min(0.7, event.intensity)

        if event.sign > 0:
            if market_state.best_ask is None:
                return None

            fraction = random.uniform(0.1, 0.25) * intensity
            quantity = int((self.money * fraction) // market_state.best_ask)
            if quantity <= 0:
                return None

            return Action(Side.BUY, market_state.best_ask, quantity, OrderType.MARKET)

        if market_state.best_bid is None:
            return None

        fraction = random.uniform(0.1, 0.25) * intensity
        quantity = int(self.shares * fraction)
        if quantity <= 0:
            return None

        return Action(Side.SELL, market_state.best_bid, quantity, OrderType.MARKET)
