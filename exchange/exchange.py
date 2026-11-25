from exchange.order import Order
from exchange.enums import OrderType
from exchange.order_book import OrderBook


class Exchange:
    """Multi-symbol exchange. Each listed symbol has its own order book."""

    def __init__(self, fee_rate=0.0, default_symbol=None):
        self.books = {}
        self.next_order_id = 1
        self.fee_rate = fee_rate
        self.default_symbol = default_symbol
        self.trade_history = []

    def list_symbol(self, symbol):
        if symbol not in self.books:
            self.books[symbol] = OrderBook(symbol)
            if self.default_symbol is None:
                self.default_symbol = symbol
        return self.books[symbol]

    def _resolve_symbol(self, symbol=None, order=None):
        if symbol is not None:
            return symbol
        if order is not None and getattr(order, "symbol", None):
            return order.symbol
        if self.default_symbol is not None:
            return self.default_symbol
        if len(self.books) == 1:
            return next(iter(self.books))
        if not self.books:
            return "DEFAULT"
        raise ValueError("symbol required when multiple books are listed")

    def get_book(self, symbol=None):
        symbol = self._resolve_symbol(symbol)
        if symbol not in self.books:
            self.list_symbol(symbol)
        return self.books[symbol]

    @property
    def order_book(self):
        """Backward-compatible view of the default symbol book."""
        return self.get_book().order_book

    @property
    def recent_prices(self):
        return self.get_book().recent_prices

    @property
    def current_volume(self):
        return self.get_book().current_volume

    def validate_order(self, order: Order):
        if order.type == OrderType.MARKET:
            if order.quantity <= 0:
                raise ValueError("Quantity Invalid")
            return
        if order.price <= 0:
            raise ValueError("Price Invalid")
        if order.quantity <= 0:
            raise ValueError("Quantity Invalid")

    def get_best_bid(self, symbol=None):
        return self.get_book(symbol).get_best_bid()

    def get_best_ask(self, symbol=None):
        return self.get_book(symbol).get_best_ask()

    def get_last_trade_price(self, symbol=None):
        return self.get_book(symbol).get_last_trade_price()

    def get_spread(self, symbol=None):
        return self.get_book(symbol).get_spread()

    def submit_order(self, order: Order, current_tick, symbol=None):
        self.validate_order(order)
        symbol = self._resolve_symbol(symbol, order)
        order.symbol = symbol
        self.list_symbol(symbol)

        order.id = self.next_order_id
        self.next_order_id += 1

        book = self.books[symbol]
        trades, cancelled = book.submit_order(order, current_tick)
        self.trade_history.extend(trades)
        return trades, cancelled

    def cancel_expired_orders(self, current_tick, symbol=None):
        if symbol is not None:
            return self.get_book(symbol).cancel_expired_orders(current_tick)

        cancelled = []
        for book in self.books.values():
            cancelled.extend(book.cancel_expired_orders(current_tick))
        return cancelled

    def cancel_trader_orders(self, trader_id, symbol=None):
        if symbol is not None:
            return self.get_book(symbol).cancel_trader_orders(trader_id)

        cancelled = []
        for book in self.books.values():
            cancelled.extend(book.cancel_trader_orders(trader_id))
        return cancelled

    def clear(self):
        for book in self.books.values():
            book.clear()
        self.trade_history = []
        self.next_order_id = 1
