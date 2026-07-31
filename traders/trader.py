import uuid
from exchange.market_state import MarketState

class Trader:
    def __init__(self, name, trader_id, money, shares, orders, strategy, stats):
        self.name = name
        self.trader_id = uuid.uuid4()
        self.money = money
        self.shares = shares
        self.orders = orders
        self.strategy = strategy
        self.stats = stats

    def decide_action():
        return
    
    def step():
        return
    
