from exchange.exchange import Exchange
from exchange.order import Order
from exchange.enums import Side, OrderType


def _limit(trader_id, side, price, qty, symbol):
    order = Order(trader_id, side, price, qty, OrderType.LIMIT)
    order.expiration_tick = 1000
    order.symbol = symbol
    return order


def test_symbol_books_are_isolated():
    exchange = Exchange()
    exchange.list_symbol("ABC")
    exchange.list_symbol("XYZ")

    exchange.submit_order(_limit("a", Side.SELL, 100, 5, "ABC"), 0, symbol="ABC")
    exchange.submit_order(_limit("b", Side.SELL, 50, 5, "XYZ"), 0, symbol="XYZ")

    assert exchange.get_best_ask("ABC") == 100
    assert exchange.get_best_ask("XYZ") == 50

    trades, _ = exchange.submit_order(_limit("c", Side.BUY, 100, 5, "ABC"), 1, symbol="ABC")
    assert len(trades) == 1
    assert trades[0].symbol == "ABC"
    assert exchange.get_best_ask("ABC") is None
    assert exchange.get_best_ask("XYZ") == 50


def test_no_cross_symbol_match():
    exchange = Exchange()
    exchange.list_symbol("ABC")
    exchange.list_symbol("XYZ")

    exchange.submit_order(_limit("s", Side.SELL, 10, 10, "ABC"), 0, symbol="ABC")
    trades, cancelled = exchange.submit_order(
        _limit("b", Side.BUY, 10, 10, "XYZ"), 1, symbol="XYZ"
    )
    assert trades == []
    assert exchange.get_best_ask("ABC") == 10
    assert exchange.get_best_bid("XYZ") == 10
