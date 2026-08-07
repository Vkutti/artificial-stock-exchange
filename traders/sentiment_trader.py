import uuid
import random

from exchange.market_state import MarketState
from traders.action import Action
from exchange.enums import Side, OrderType

class SentimentTrader:
    def __init__(self, name, money, shares, orders):
            self.name = name
            self.trader_id = uuid.uuid4()

            self.money = money
            self.shares = shares
            self.orders = orders

            self.activity_rate = random.uniform(0.05, 0.15)

            self.order_ttl = random.randint(30, 300)

            self.average_wait = random.randint(10, 35)

    def decide_action(self, market_state: MarketState):
        if random.random() > self.activity_rate:
            return None
        
        company_sentiment = market_state.company.sentiment

        if company_sentiment < 0:
            return
        elif company_sentiment > 0:
            return
        else:
            return None