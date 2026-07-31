from itertools import count
from exchange.order import Order
from exchange.enums import Side, OrderStatus
from exchange.trade import Trade
import time

class Exchange:
    _id_generator = count(1)  
    
    def __init__(self):
        self.order_book = {Side.BUY: {}, Side.SELL: {}}

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

    def get_opposite_book(self, order: Order):
        if order.side == Side.BUY:
            return self.order_book[Side.SELL], Side.SELL

        else:
            return self.order_book[Side.BUY], Side.BUY
        
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
        ask = self.get_best_ask()
        bid = self.get_best_bid()

        if ask is None or bid is None:
            return None 

        return (ask - bid)
        
    def create_trade(self, order: Order, other_order, best_price, trade_quantity):
        if order.side == Side.BUY:
            trade = Trade(order.trader_id, other_order.trader_id, best_price, trade_quantity, time.time())
        else:
            trade = Trade(other_order.trader_id, order.trader_id, best_price, trade_quantity, time.time())

        return trade

    def match_order(self, order: Order):
        trades = []

        while order.remaining_quantity > 0:
            best_price = self.get_best_price(order)

            if best_price is None:
                break

            if order.side == Side.BUY and order.price < best_price:
                break

            if order.side == Side.SELL and order.price > best_price:
                break

            other_side = Side.SELL if order.side == Side.BUY else Side.BUY
            other_order = self.order_book[other_side][best_price][0]

            trade_quantity = min(order.remaining_quantity, other_order.remaining_quantity)

            order.remaining_quantity -= trade_quantity
            other_order.remaining_quantity -= trade_quantity

            trade = self.create_trade(order, other_order, best_price, trade_quantity)

            self.trade_history.append(trade)
            trades.append(trade)

            if other_order.remaining_quantity == 0:
                self.order_book[other_side][best_price].pop(0)

                if len(self.order_book[other_side][best_price]) == 0:
                    del self.order_book[other_side][best_price]

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
            if order.price >= best_price:
                return True
        else:
            if order.price <= best_price:
                return True
            
        return False
        
    def submit_order(self, order: Order):
        self.validate_order(order)

        order.id = self.next_order_id
        self.next_order_id += 1

        can_match = self.check_match(order)

        if can_match:
            self.match_order(order)

        if order.remaining_quantity > 0:
            self.add_order_to_book(order)

        return order