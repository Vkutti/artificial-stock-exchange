from exchange.enums import Side, OrderStatus, OrderType
from exchange.trade import Trade


class OrderBook:
    """Single-symbol limit order book."""

    def __init__(self, symbol):
        self.symbol = symbol
        self.order_book = {
            Side.BUY: {},
            Side.SELL: {},
        }
        self.trade_history = []
        self.recent_prices = []
        self.current_volume = 0

    def add_order_to_book(self, order):
        side_book = self.order_book[order.side]
        if order.price not in side_book:
            side_book[order.price] = []
        side_book[order.price].append(order)

    def get_best_price(self, order):
        if order.side == Side.BUY:
            sell_book = self.order_book[Side.SELL]
            if not sell_book:
                return None
            return min(sell_book.keys())

        buy_book = self.order_book[Side.BUY]
        if not buy_book:
            return None
        return max(buy_book.keys())

    def get_best_bid(self):
        buy_book = self.order_book[Side.BUY]
        if not buy_book:
            return None
        return max(buy_book.keys())

    def get_best_ask(self):
        sell_book = self.order_book[Side.SELL]
        if not sell_book:
            return None
        return min(sell_book.keys())

    def get_last_trade_price(self):
        if not self.trade_history:
            return None
        return self.trade_history[-1].price

    def get_spread(self):
        bid = self.get_best_bid()
        ask = self.get_best_ask()
        if bid is None or ask is None:
            return None
        return ask - bid

    def create_trade(
        self,
        order,
        other_order,
        price,
        quantity,
        current_tick,
        buyer_reservation_release=0.0,
        seller_shares_release=0,
    ):
        if order.side == Side.BUY:
            return Trade(
                order.trader_id,
                other_order.trader_id,
                price,
                quantity,
                current_tick,
                current_tick,
                buyer_reservation_release,
                seller_shares_release,
                symbol=self.symbol,
            )
        return Trade(
            other_order.trader_id,
            order.trader_id,
            price,
            quantity,
            current_tick,
            current_tick,
            buyer_reservation_release,
            seller_shares_release,
            symbol=self.symbol,
        )

    def _crosses(self, order, best_price):
        if order.type == OrderType.MARKET:
            if order.side == Side.BUY:
                if getattr(order, "reserved_cash", 0) > 0:
                    return order.price >= best_price
                return True
            if getattr(order, "reserved_shares", 0) > 0:
                return order.price <= best_price
            return True
        if order.side == Side.BUY:
            return order.price >= best_price
        return order.price <= best_price

    def _consume_buy_reservation(self, buy_order, trade_quantity):
        if buy_order.remaining_quantity <= 0 or buy_order.reserved_cash <= 0:
            return 0.0
        release = buy_order.reserved_cash * (trade_quantity / buy_order.remaining_quantity)
        buy_order.reserved_cash = max(0.0, buy_order.reserved_cash - release)
        return release

    def _consume_sell_reservation(self, sell_order, trade_quantity):
        if sell_order.reserved_shares <= 0:
            return 0
        release = min(trade_quantity, sell_order.reserved_shares)
        sell_order.reserved_shares -= release
        return release

    def check_match(self, order):
        best_price = self.get_best_price(order)
        if best_price is None:
            return False
        return self._crosses(order, best_price)

    def match_order(self, order, current_tick):
        trades = []
        cancelled = []

        while order.remaining_quantity > 0:
            best_price = self.get_best_price(order)
            if best_price is None:
                break
            if not self._crosses(order, best_price):
                break

            opposite_side = Side.SELL if order.side == Side.BUY else Side.BUY
            price_level = self.order_book[opposite_side][best_price]

            if not price_level:
                del self.order_book[opposite_side][best_price]
                continue

            resting_order = price_level[0]

            if resting_order.trader_id == order.trader_id:
                price_level.pop(0)
                resting_order.status = OrderStatus.CANCELLED
                cancelled.append(resting_order)
                if len(price_level) == 0:
                    del self.order_book[opposite_side][best_price]
                continue

            trade_quantity = min(order.remaining_quantity, resting_order.remaining_quantity)

            if order.side == Side.BUY:
                buy_order, sell_order = order, resting_order
            else:
                buy_order, sell_order = resting_order, order

            buyer_release = self._consume_buy_reservation(buy_order, trade_quantity)
            seller_release = self._consume_sell_reservation(sell_order, trade_quantity)

            order.remaining_quantity -= trade_quantity
            resting_order.remaining_quantity -= trade_quantity

            trade = self.create_trade(
                order,
                resting_order,
                best_price,
                trade_quantity,
                current_tick,
                buyer_release,
                seller_release,
            )
            self.trade_history.append(trade)
            self.recent_prices.append(trade.price)
            if len(self.recent_prices) > 1000:
                self.recent_prices.pop(0)
            self.current_volume += trade_quantity
            trades.append(trade)

            if resting_order.remaining_quantity == 0:
                resting_order.status = OrderStatus.FILLED
                price_level.pop(0)
                if len(price_level) == 0:
                    del self.order_book[opposite_side][best_price]
            else:
                resting_order.status = OrderStatus.PARTIALLY_FILLED

        if order.remaining_quantity == 0:
            order.status = OrderStatus.FILLED
        elif order.remaining_quantity < order.quantity:
            order.status = OrderStatus.PARTIALLY_FILLED
        else:
            order.status = OrderStatus.NEW

        return trades, cancelled

    def submit_order(self, order, current_tick):
        trades = []
        cancelled = []

        if self.check_match(order):
            trades, cancelled = self.match_order(order, current_tick)

        if order.type == OrderType.MARKET:
            if order.remaining_quantity > 0:
                if order.remaining_quantity < order.quantity:
                    order.status = OrderStatus.PARTIALLY_FILLED
                else:
                    order.status = OrderStatus.CANCELLED
                cancelled.append(order)
            return trades, cancelled

        if order.remaining_quantity > 0:
            self.add_order_to_book(order)

        return trades, cancelled

    def cancel_expired_orders(self, current_tick):
        cancelled = []
        for side in (Side.BUY, Side.SELL):
            side_book = self.order_book[side]
            for price in list(side_book.keys()):
                active_orders = []
                for order in side_book[price]:
                    if order.expiration_tick is None:
                        active_orders.append(order)
                        continue
                    if current_tick >= order.expiration_tick:
                        order.status = OrderStatus.CANCELLED
                        cancelled.append(order)
                    else:
                        active_orders.append(order)
                if active_orders:
                    side_book[price] = active_orders
                else:
                    del side_book[price]
        return cancelled

    def cancel_trader_orders(self, trader_id):
        cancelled = []
        for side in (Side.BUY, Side.SELL):
            side_book = self.order_book[side]
            for price in list(side_book.keys()):
                remaining_orders = []
                for order in side_book[price]:
                    if order.trader_id == trader_id:
                        order.status = OrderStatus.CANCELLED
                        cancelled.append(order)
                    else:
                        remaining_orders.append(order)
                if remaining_orders:
                    side_book[price] = remaining_orders
                else:
                    del side_book[price]
        return cancelled

    def clear(self):
        self.order_book = {Side.BUY: {}, Side.SELL: {}}
        self.trade_history = []
        self.recent_prices = []
        self.current_volume = 0
