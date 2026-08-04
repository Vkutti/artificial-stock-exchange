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

        self.quote_interval = random.randint(3, 7)

        self.last_quote_tick = -1

        self.order_ttl = 10

        self.target_inventory = shares

        self.inventory_factor = 8

        self.base_spread = 2

        self.min_order_size = 5
        self.max_order_size = 20

        self.next_action_tick = 0
        self.average_wait = 1

        self.fair_value_offset = random.gauss(0, 5)        

    def decide_action(self, market_state: MarketState):
        current_tick = market_state.current_tick

        if current_tick - self.last_quote_tick < self.quote_interval:
            return None
        
        fair_value = (market_state.fundamental_price + self.fair_value_offset)

        self.last_quote_tick = current_tick

        if (market_state.best_bid is not None and market_state.best_ask is not None):
            mid_price = (market_state.best_bid + market_state.best_ask) / 2
        elif market_state.last_trade_price is not None:
            mid_price = market_state.last_trade_price
        else:
            mid_price = fair_value

        recent_prices = market_state.recent_prices[-50:]

        if len(recent_prices) >= 2:
            volatility = np.std(recent_prices)
        else:
            volatility = 0

        spread = self.base_spread + volatility * 0.5

        inventory_difference = (self.shares - self.target_inventory)

        inventory_ratio = (inventory_difference / max(self.target_inventory, 1))

        inventory_skew = (inventory_ratio * self.inventory_factor)

        bid_price = (mid_price - spread - inventory_skew)

        ask_price = (mid_price + spread - inventory_skew)

        bid_price = max(1, round(bid_price))
        ask_price = max(bid_price + 1, round(ask_price))
 
        actions = []

        if inventory_difference > 0:
            bid_quantity = random.randint(1, self.min_order_size)

            ask_quantity = random.randint(self.min_order_size, self.max_order_size)
        elif inventory_difference < 0:
            bid_quantity = random.randint(self.min_order_size, self.max_order_size)

            ask_quantity = random.randint(1, self.min_order_size)
        else:
            bid_quantity = max(1, int(20 * np.exp(-abs(inventory_ratio))))

            ask_quantity = max(1, int(20 * np.exp(-abs(inventory_ratio))))

        if self.money >= bid_price * bid_quantity:
            actions.append(Action(Side.BUY, bid_price, bid_quantity, OrderType.LIMIT))

        if self.shares >= ask_quantity:
            actions.append(Action( Side.SELL, ask_price, ask_quantity, OrderType.LIMIT))

        return actions