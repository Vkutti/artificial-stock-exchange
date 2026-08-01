from itertools import count
from exchange.order import Order
from exchange.enums import Side, OrderStatus
from exchange.trade import Trade
import time

class Exchange:
    _id_generator = count(1)

    def __init__(self):

        self.order_book = {
            Side.BUY: {},
            Side.SELL: {}
        }

        self.trade_history = []

        self.next_order_id = 1

        self.recent_prices = []

        self.current_volume = 0

    def validate_order(self, order: Order):
        if order.price <= 0:
            raise ValueError("Price Invalid")

        if order.quantity <= 0:
            raise ValueError("Quantity Invalid")

    def add_order_to_book(self, order: Order):
        side_book = self.order_book[order.side]

        if order.price not in side_book:
            side_book[order.price] = []

        side_book[order.price].append(order)

    def get_best_price(self, order: Order):
        if order.side == Side.BUY:
            sell_book = self.order_book[Side.SELL]

            if not sell_book:
                return None

            return min(sell_book.keys())
        else:
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

    def create_trade(self, order: Order, other_order: Order, price, quantity):
        if order.side == Side.BUY:
            return Trade(order.trader_id, other_order.trader_id, price, quantity, time.time())
        else:
            return Trade(other_order.trader_id, order.trader_id, price, quantity, time.time())

    def match_order(self, order: Order):
        trades = []

        while order.remaining_quantity > 0:
            best_price = self.get_best_price(order)

            if best_price is None:
                break

            if order.side == Side.BUY:
                if order.price < best_price:
                    break
            else:
                if order.price > best_price:
                    break

            opposite_side = (Side.SELL if order.side == Side.BUY else Side.BUY)

            price_level = (self.order_book[opposite_side][best_price])

            if not price_level:
                del self.order_book[opposite_side][best_price]
                continue

            resting_order = price_level[0]

            trade_quantity = min(order.remaining_quantity, resting_order.remaining_quantity)

            order.remaining_quantity -= trade_quantity

            resting_order.remaining_quantity -= trade_quantity

            trade = self.create_trade(order, resting_order, best_price, trade_quantity)

            self.trade_history.append(trade)

            self.recent_prices.append(trade.price)

            if len(self.recent_prices) > 1000:
                self.recent_prices.pop(0)

            self.current_volume += (trade_quantity)

            trades.append(trade)

            if resting_order.remaining_quantity == 0:
                price_level.pop(0)

                if len(price_level) == 0:
                    del self.order_book[opposite_side][best_price]

        if order.remaining_quantity == 0:
            order.status = OrderStatus.FILLED
        elif order.remaining_quantity < order.quantity:
            order.status = OrderStatus.PARTIALLY_FILLED
        else:
            order.status = OrderStatus.NEW

        return trades

    def check_match(self, order: Order):
        best_price = self.get_best_price(order)

        if best_price is None:
            return False

        if order.side == Side.BUY:
            return order.price >= best_price
        else:
            return order.price <= best_price

    def submit_order(self, order: Order):
        self.validate_order(order)

        order.id = self.next_order_id

        self.next_order_id += 1

        trades = []

        if self.check_match(order):
            trades = self.match_order(order)

        if order.remaining_quantity > 0:
            self.add_order_to_book(order)

        return trades

    def cancel_expired_orders(self, current_tick):
        cancelled = []

        for side in (Side.BUY, Side.SELL):
            side_book = self.order_book[side]

            for price in list(side_book.keys()):
                active_orders = []

                for order in side_book[price]:
                    if (current_tick >= order.expiration_tick):
                        order.status = (OrderStatus.CANCELLED)

                        cancelled.append(order)
                    else:
                        active_orders.append(order)

                if active_orders:
                    side_book[price] = active_orders
                else:
                    del side_book[price]



        return cancelled