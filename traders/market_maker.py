import uuid

from exchange.market_state import MarketState
from traders.action import Action
from exchange.enums import Side, OrderType
from exchange.ticks import DEFAULT_TICK_SIZE, round_to_tick, spread_from_bps

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

        # Relative spread in basis points of mid (~0.35%; keeps NBBO ~10–80 bps)
        self.base_spread_bps = 35.0
        self.max_spread_bps = 150.0
        # Inventory skew in bps of mid per unit inventory ratio
        self.inventory_skew_bps = 12.0
        self.tick_size = DEFAULT_TICK_SIZE

        # Times are in trading minutes
        self.order_ttl = 5
        self.average_wait = 2
        self.quote_interval = 2
        self.last_quote_tick = -999
        self.symbol = None

        self.min_size = 5
        self.max_size = 20

        # Offset as fraction of fundamental (~±0.5%)
        self.fair_value_offset_bps = random.gauss(0, 50)

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

        fv = market_state.fundamental_price
        fundamental = fv * (1.0 + self.fair_value_offset_bps / 10000.0)

        if market_mid is None:
            fair = fundamental
        else:
            fair = 0.8 * fundamental + 0.2 * market_mid

        fair = max(self.tick_size, fair)

        prices = np.array(market_state.recent_prices[-50:], dtype=float)

        if len(prices) > 5:
            returns = np.diff(prices) / np.maximum(prices[:-1], 1e-9)
            volatility = float(np.std(returns))
        else:
            volatility = 0.0

        # Widen with realized vol; keep within max_spread_bps
        vol_bps = min(self.max_spread_bps, volatility * 10000.0 * 0.5)
        spread_bps = min(self.max_spread_bps, max(10.0, self.base_spread_bps + vol_bps))
        # At least enough ticks to realize ~10 bps at current fair
        min_ticks = max(2, int(np.ceil((fair * 0.0010) / self.tick_size)))
        spread = spread_from_bps(
            fair,
            spread_bps,
            tick_size=self.tick_size,
            min_ticks=min_ticks,
            max_bps=self.max_spread_bps,
        )

        inventory_error = self.shares - self.target_inventory
        inventory_ratio = inventory_error / max(self.target_inventory, 1)
        skew = fair * (inventory_ratio * self.inventory_skew_bps / 10000.0)

        bid = fair - spread / 2 - skew
        ask = fair + spread / 2 - skew

        bid = round_to_tick(max(self.tick_size, bid), self.tick_size)
        ask = round_to_tick(max(bid + self.tick_size, ask), self.tick_size)
        if ask <= bid:
            ask = round_to_tick(bid + self.tick_size, self.tick_size)

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
