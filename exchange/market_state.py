class PublicHeadline:
    __slots__ = ("tick", "kind", "source", "headline", "symbol", "sign", "intensity")

    def __init__(self, tick, kind, source, headline, symbol, sign, intensity):
        self.tick = tick
        self.kind = kind
        self.source = source
        self.headline = headline
        self.symbol = symbol
        self.sign = sign
        self.intensity = intensity

    @property
    def magnitude(self):
        return self.sign * 0.03 * self.intensity


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
        company=None,
        recent_events=None,
        clock=None,
        time_label=None,
        symbol=None,
        sentiment_value=0.0,
        sentiment_history=None,
        imbalance=0.0,
        halted=False,
        session_phase="continuous",
        flow_multiplier=1.0,
        risk_free_rate=0.05,
    ):
        self.best_bid = best_bid
        self.best_ask = best_ask
        self.last_trade_price = last_trade_price
        self.spread = spread
        self.recent_prices = list(recent_prices) if recent_prices is not None else []
        self.current_tick = current_tick
        self.fundamental_price = fundamental_price
        self.volume = volume
        self.company = company
        self.recent_events = recent_events if recent_events is not None else []
        self.clock = clock
        self.time_label = time_label
        self.symbol = symbol
        self.sentiment_value = sentiment_value
        self.sentiment_history = list(sentiment_history) if sentiment_history is not None else []
        self.imbalance = imbalance
        self.halted = halted
        self.session_phase = session_phase
        self.flow_multiplier = flow_multiplier
        self.risk_free_rate = risk_free_rate
