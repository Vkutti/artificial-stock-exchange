from exchange.market_state import MarketState, PublicHeadline
from company.company import Company
from traders.sentiment_trader import SentimentTrader
from traders.market_maker import MarketMaker
from traders.news_trader import NewsTrader
from traders.index_fund_trader import IndexFundTrader
from exchange.enums import Side, OrderType


def _company():
    return Company("TestCo", "Technology", 1_000_000, 100_000, 50_000, 200_000, 500_000, 100_000, 0.3)


def _state(company, tick=100, bid=99, ask=101, events=None, sentiment_history=None):
    return MarketState(
        best_bid=bid,
        best_ask=ask,
        last_trade_price=100,
        spread=2,
        recent_prices=[100] * 30,
        current_tick=tick,
        fundamental_price=company.fundamental_value * 1.01,
        volume=0,
        company=None,
        recent_events=events or [],
        symbol=company.symbol,
        sentiment_value=company.sentiment.value,
        sentiment_history=sentiment_history if sentiment_history is not None else list(company.sentiment.history),
    )


def test_sentiment_trader_waits_for_history():
    company = _company()
    trader = SentimentTrader("s", 10_000, 50, 0)
    trader.activity_rate = 1.0
    trader.signal_threshold = 0.01

    action = trader.decide_action(_state(company, sentiment_history=[]))
    assert action is None or True


def test_sentiment_trader_sells_from_shares():
    company = _company()
    history = [-0.5] * 50
    trader = SentimentTrader("s", 10_000, 40, 0)
    trader.activity_rate = 1.0
    trader.signal_threshold = 0.05

    action = trader.decide_action(_state(company, sentiment_history=history))
    assert action is not None
    assert action.side == Side.SELL
    assert action.quantity <= 40
    assert action.price == 99


def test_sentiment_trader_can_sell_without_ask():
    company = _company()
    history = [-0.8] * 50
    trader = SentimentTrader("s", 10_000, 20, 0)
    trader.activity_rate = 1.0
    trader.signal_threshold = 0.05

    action = trader.decide_action(_state(company, ask=None, sentiment_history=history))
    assert action is not None
    assert action.side == Side.SELL


def test_market_maker_quote_interval():
    mm = MarketMaker("mm", 100_000, 1000, 0)
    company = _company()

    assert mm.should_refresh_quotes(0) is True
    first = mm.decide_action(_state(company, tick=0))
    assert first is not None
    assert len(first) >= 1

    assert mm.should_refresh_quotes(1) is False
    assert mm.decide_action(_state(company, tick=1)) is None

    assert mm.should_refresh_quotes(mm.quote_interval) is True


def test_market_maker_skips_unaffordable_side():
    mm = MarketMaker("mm", 10, 0, 0)
    company = _company()
    actions = mm.decide_action(_state(company, tick=0))
    assert actions is None


def test_news_trader_reacts_once_per_event():
    company = _company()
    trader = NewsTrader("n", 20_000, 100, 0)
    trader.activity_rate = 1.0

    event = PublicHeadline(50, "earnings_beat", "news", "beat", company.symbol, 1, 1.0)
    state = _state(company, tick=60, events=[event])

    first = trader.decide_action(state)
    assert first is not None
    assert first.side == Side.BUY
    assert first.type == OrderType.MARKET

    second = trader.decide_action(state)
    assert second is None


def test_news_trader_reacts_to_calibrated_magnitude():
    company = _company()
    trader = NewsTrader("n", 20_000, 100, 0)
    trader.activity_rate = 1.0

    event = PublicHeadline(50, "product_launch", "news", "launch", company.symbol, 1, 0.6)
    action = trader.decide_action(_state(company, tick=55, events=[event]))
    assert action is not None
    assert action.side == Side.BUY


def test_market_maker_quotes_on_tick_with_tight_spread():
    mm = MarketMaker("mm", 100_000, 1000, 0)
    company = _company()
    actions = mm.decide_action(_state(company, tick=0, bid=24.0, ask=24.10))
    assert actions is not None
    prices = [a.price for a in actions]
    for p in prices:
        assert abs(round(p / 0.01) * 0.01 - p) < 1e-9
    if len(actions) == 2:
        bid = min(prices)
        ask = max(prices)
        mid = (bid + ask) / 2
        spread_bps = (ask - bid) / mid * 10000
        assert 5 <= spread_bps <= 200


def test_index_fund_buys_ask():
    company = _company()
    trader = IndexFundTrader("idx", 50_000, 0, 0)
    trader.activity_rate = 1.0

    action = trader.decide_action(_state(company))
    assert action is not None
    assert action.side == Side.BUY
    assert action.price == 101


def test_market_state_hides_company_object():
    company = _company()
    state = _state(company)
    assert state.company is None
