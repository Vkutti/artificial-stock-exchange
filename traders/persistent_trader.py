import uuid
import random

from exchange.market_state import MarketState
from traders.action import Action
from exchange.enums import Side, OrderType

class PersistentTrader:
    def __init__(self, name, money, shares, orders):
            self.name = name
            self.trader_id = uuid.uuid4()

            self.money = money
            self.shares = shares
            self.orders = orders

            self.activity_rate = random.uniform(0.01, 0.05)

            self.order_ttl = random.randint(30, 300)

            self.average_wait = random.randint(30, 45)

    def decide_action(self, market_state: MarketState):
        if random.random() > self.activity_rate:
            return None
        
        if (market_state.best_bid is not None and market_state.best_ask is not None):
            current_price = (market_state.best_bid + market_state.best_ask) / 2
        elif market_state.last_trade_price is not None:
            current_price = (market_state.last_trade_price)
        else:
            current_price = 100
        
        max_quantity = int((0.15 * self.money) // current_price)
        
        if max_quantity <= 0:
            return None
        
        if market_state.best_ask is None:
            return None
        
        return Action(Side.BUY, market_state.best_ask, max_quantity, OrderType.MARKET)