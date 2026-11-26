from exchange.exchange import Exchange
from exchange.order import Order
from exchange.enums import Side, OrderType, OrderStatus


def _limit(trader_id, side, price, qty):
    order = Order(trader_id, side, price, qty, OrderType.LIMIT)
    order.expiration_tick = 1000
    return order


def _market(trader_id, side, qty, price=1):
    order = Order(trader_id, side, price, qty, OrderType.MARKET)
    order.expiration_tick = 1000
    return order


def test_price_time_priority_and_partial_fill():
    exchange = Exchange()
    exchange.list_symbol("TEST")

    sell_a = _limit("s1", Side.SELL, 100, 5)
    sell_b = _limit("s2", Side.SELL, 100, 10)
    exchange.submit_order(sell_a, 0)
    exchange.submit_order(sell_b, 0)

    buy = _limit("b1", Side.BUY, 100, 8)
    trades, cancelled = exchange.submit_order(buy, 1)

    assert len(cancelled) == 0
    assert len(trades) == 2
    assert trades[0].quantity == 5
    assert trades[0].sell_trader_id == "s1"
    assert trades[1].quantity == 3
    assert trades[1].sell_trader_id == "s2"
    assert sell_a.status == OrderStatus.FILLED
    assert sell_b.status == OrderStatus.PARTIALLY_FILLED
    assert sell_b.remaining_quantity == 7
    assert buy.status == OrderStatus.FILLED


def test_market_order_sweeps_and_does_not_rest():
    exchange = Exchange()

    exchange.submit_order(_limit("s1", Side.SELL, 90, 4), 0)
    exchange.submit_order(_limit("s2", Side.SELL, 95, 10), 0)

    buy = _market("b1", Side.BUY, 6)
    trades, cancelled = exchange.submit_order(buy, 1)

    assert len(trades) == 2
    assert sum(t.quantity for t in trades) == 6
    assert buy.remaining_quantity == 0
    assert buy.status == OrderStatus.FILLED
    assert Side.BUY not in exchange.order_book or exchange.order_book[Side.BUY] == {}
    assert exchange.get_best_ask() == 95


def test_unfilled_market_order_is_cancelled():
    exchange = Exchange()

    buy = _market("b1", Side.BUY, 5)
    trades, cancelled = exchange.submit_order(buy, 0)

    assert trades == []
    assert buy in cancelled
    assert buy.status == OrderStatus.CANCELLED
    assert exchange.order_book[Side.BUY] == {}


def test_self_trade_cancels_resting_order():
    exchange = Exchange()

    resting = _limit("t1", Side.SELL, 50, 10)
    exchange.submit_order(resting, 0)

    aggressor = _limit("t1", Side.BUY, 50, 5)
    trades, cancelled = exchange.submit_order(aggressor, 1)

    assert trades == []
    assert resting in cancelled
    assert resting.status == OrderStatus.CANCELLED
    assert aggressor.remaining_quantity == 5
    assert aggressor.status == OrderStatus.NEW
    assert exchange.get_best_ask() is None


def test_expiration_skips_none_and_cancels_due():
    exchange = Exchange()

    forever = _limit("a", Side.SELL, 10, 1)
    forever.expiration_tick = None
    due = _limit("b", Side.SELL, 11, 1)
    due.expiration_tick = 5

    exchange.submit_order(forever, 0)
    exchange.submit_order(due, 0)

    cancelled = exchange.cancel_expired_orders(5)

    assert due in cancelled
    assert due.status == OrderStatus.CANCELLED
    assert exchange.get_best_ask() == 10


def test_best_bid_ask_and_spread():
    exchange = Exchange()

    exchange.submit_order(_limit("b", Side.BUY, 98, 1), 0)
    exchange.submit_order(_limit("s", Side.SELL, 102, 1), 0)

    assert exchange.get_best_bid() == 98
    assert exchange.get_best_ask() == 102
    assert exchange.get_spread() == 4


def test_limit_price_snaps_to_tick():
    from exchange.ticks import round_to_tick

    assert round_to_tick(10.124) == 10.12
    assert round_to_tick(10.126) == 10.13
    assert round_to_tick(0.004) == 0.01

    exchange = Exchange(tick_size=0.01)
    order = _limit("b", Side.BUY, 24.126, 1)
    exchange.submit_order(order, 0)

    assert order.price == 24.13
    assert exchange.get_best_bid() == 24.13
