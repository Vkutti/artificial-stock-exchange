from company.company import Company


class MarketState:
    def __init__(
        self,
        best_bid,
        best_ask,
        last_trade_price,
        spread,
        recent_prices,
        current_tick,
        fundamental_price,
        volume,
        company: Company,
        recent_events=None,
        clock=None,
        time_label=None,
        symbol=None,
    ):
        self.best_bid = best_bid
        self.best_ask = best_ask
        self.last_trade_price = last_trade_price
        self.spread = spread
        self.recent_prices = recent_prices
        self.current_tick = current_tick  # trading-minute index
        self.fundamental_price = fundamental_price
        self.volume = volume
        self.company = company
        self.recent_events = recent_events if recent_events is not None else []
        self.clock = clock
        self.time_label = time_label
        self.symbol = symbol or (company.symbol if company is not None else None)
