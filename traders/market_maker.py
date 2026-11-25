import uuid

from exchange.market_state import MarketState
from traders.action import Action
from exchange.enums import Side, OrderType

import random
import numpy as np


class MarketMaker:
    def __init__(self, name, money, shares, orders):
        self.name = name
        self.trader_id = uuid.uuid4()

        self.money = money
        self.shares = shares
        self.orders = orders

        self.target_inventory = shares

        self.base_spread = 2
        self.inventory_factor = 5

        # Times are in trading minutes
        self.order_ttl = 5
        self.average_wait = 2
        self.quote_interval = 2
        self.last_quote_tick = -999
        self.symbol = None

        self.min_size = 5
        self.max_size = 20

        self.fair_value_offset = random.gauss(0, 2)

    def should_refresh_quotes(self, tick):
        return tick - self.last_quote_tick >= self.quote_interval

    def decide_action(self, market_state):
        tick = market_state.current_tick

        if not self.should_refresh_quotes(tick):
            return None

        self.last_quote_tick = tick

        market_mid = None

        if market_state.best_bid is not None and market_state.best_ask is not None:
            market_mid = (market_state.best_bid + market_state.best_ask) / 2
        elif market_state.last_trade_price is not None:
            market_mid = market_state.last_trade_price

        fundamental = market_state.fundamental_price + self.fair_value_offset

        if market_mid is None:
            fair = fundamental
        else:
            fair = 0.8 * fundamental + 0.2 * market_mid

        prices = np.array(market_state.recent_prices[-50:])

        if len(prices) > 5:
            returns = np.diff(prices) / prices[:-1]
            volatility = np.std(returns)
        else:
            volatility = 0

        spread = max(
            self.base_spread,
            self.base_spread + volatility * fair * 1.5,
        )

        inventory_error = self.shares - self.target_inventory
        inventory_ratio = inventory_error / max(self.target_inventory, 1)
        skew = inventory_ratio * self.inventory_factor

        bid = fair - spread / 2 - skew
        ask = fair + spread / 2 - skew

        bid = max(1, round(bid))
        ask = max(bid + 1, round(ask))

        base = random.randint(self.min_size, self.max_size)
        bid_size = base
        ask_size = base

        if inventory_ratio > 0:
            ask_size = int(base * 1.5)
            bid_size = int(base * 0.5)
        elif inventory_ratio < 0:
            bid_size = int(base * 1.5)
            ask_size = int(base * 0.5)

        bid_size = max(1, bid_size)
        ask_size = max(1, ask_size)

        actions = []

        bid_cost = bid * bid_size
        if self.money >= bid_cost and bid_size > 0:
            actions.append(Action(Side.BUY, bid, bid_size, OrderType.LIMIT))

        if self.shares >= ask_size and ask_size > 0:
            actions.append(Action(Side.SELL, ask, ask_size, OrderType.LIMIT))

        if not actions:
            return None

        return actions
