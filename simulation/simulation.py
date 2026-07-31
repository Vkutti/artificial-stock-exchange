from exchange.exchange import Exchange
from exchange.market_state import MarketState
from traders.trader import Trader

class Simulation():
    def __init__(self, exchange: Exchange):
        return 

    def build_market_stats(self):
        market_state = MarketState(
            best_bid=self.exchange.get_best_bid(),
            best_ask=self.exchange.get_best_ask(),
            last_trade_price=self.exchange.get_last_trade_price(),
            spread=self.exchange.get_spread(),
            recent_prices=self.exchange.recent_prices,
            current_tick=self.current_tick,
            volume=self.exchange.current_volume
        )

        return market_state
    
    def run(self):
        return