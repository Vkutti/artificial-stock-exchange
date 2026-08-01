from exchange.exchange import Exchange
from exchange.order import Order
from exchange.enums import Side, OrderType

# exchange = Exchange()

# print(exchange.order_book)

# exchange.submit_order(Order(1234, Side.SELL, 100, 10, OrderType.MARKET))
# exchange.submit_order(Order(1235, Side.SELL, 120, 20, OrderType.MARKET))
# exchange.submit_order(Order(1236, Side.SELL, 90, 15, OrderType.MARKET))

# exchange.submit_order(Order(1237, Side.BUY, 105, 5, OrderType.MARKET))
# exchange.submit_order(Order(1238, Side.BUY, 110, 10, OrderType.MARKET))
# exchange.submit_order(Order(1239, Side.BUY, 120, 10, OrderType.MARKET))

# print((exchange.order_book[Side.SELL][120][0]))

def test_empty_book():
    exchange = Exchange()

    exchange.submit_order(Order(1234, Side.SELL, 100, 10, OrderType.MARKET))
    exchange.submit_order(Order(1235, Side.SELL, 120, 20, OrderType.MARKET))
    exchange.submit_order(Order(1236, Side.SELL, 90, 15, OrderType.MARKET))

    exchange.submit_order(Order(1237, Side.BUY, 105, 5, OrderType.MARKET))
    exchange.submit_order(Order(1238, Side.BUY, 110, 10, OrderType.MARKET))
    exchange.submit_order(Order(1239, Side.BUY, 120, 10, OrderType.MARKET))

    return (exchange.order_book)

    # assert exchange.order_book == {
    #     Side.BUY: {},
    #     Side.SELL: {}
    # }