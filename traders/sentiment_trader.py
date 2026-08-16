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

            self.activity_rate = random.uniform(0.05, 0.2)

            self.order_ttl = random.randint(30, 300)

            self.average_wait = random.randint(5, 20)

    def decide_action(self, market_state: MarketState):
        if random.random() > self.activity_rate:
            return None
    

        short_term = market_state.company.sentiment.history[-5:]
        long_term = market_state.company.sentiment.history[-50:]

        short_avg = sum(short_term) / len(short_term)
        long_avg = sum(long_term) / len(long_term)

        signal = 0.7 * short_avg + 0.3 * long_avg

        if len(market_state.company.sentiment.history) < 50:
            signal = 0
        
        if (market_state.best_bid is not None and market_state.best_ask is not None):
            current_price = (market_state.best_bid + market_state.best_ask) / 2
        elif market_state.last_trade_price is not None:
            current_price = (market_state.last_trade_price)
        else:
            current_price = 20


        if (market_state.best_ask == None):
            return None

        max_affordable = int((random.uniform(0.2, 0.5) * self.money) // market_state.best_ask)

        if max_affordable <= 0:
            return None

        max_quantity = random.randint(1, max_affordable)

        if signal < 0:
            return Action(Side.SELL, current_price, max_quantity, OrderType.MARKET)
        elif signal > 0:
            return Action(Side.BUY, current_price, max_quantity, OrderType.MARKET)
        else:
            return None