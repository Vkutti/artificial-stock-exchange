class MarketState:
    def __init__(self, best_bid, best_ask, last_trade_price, spread, recent_prices, current_tick, fundamental_price, volume):
        self.best_bid = best_bid
        self.best_ask = best_ask
        self.last_trade_price = last_trade_price
        self.spread = spread
        self.recent_prices = recent_prices
        self.current_tick = current_tick
        self.fundamental_price = fundamental_price
        self.volume = volume