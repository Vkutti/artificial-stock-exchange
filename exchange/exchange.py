from itertools import count
from order import Order
from enums import Side
from trade import Trade
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
        
    def get_best_price(self, order):
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

    def match_order(self, order: Order, best, other_side):
        current_book = self.order_book[order.side]
        other_book = self.order_book[other_side]

        while order.remaining_quantity > 0:
            other_order = other_book[best][0]
            
            if order.remaining_quantity >= other_order.remaining_quantity:
                order.remaining_quantity -= other_order.remaining_quantity
            elif order.remaining_quantity < other_order.remaining_quantity:
                other_order -= order.remaining_quantity
                order.remaining_quantity = 0
            
            if (other_side == Side.SELL):
                self.trade_history.append(Trade(order.trader_id, other_order.trader_id, other_order.price, other_order.quantity, time.time()))
            else:
                self.trade_history.append(Trade(other_order.trader_id, order.trader_id, order.price, order.quantity, time.time()))

            other_book[best].delete(other_book[best][0])
        
        return
    
        
    def submit_order(self, order: Order):
        self.validate_order(order)

        order.id = self.next_order_id
        self.next_order_id += 1

        best_price = self.get_best_price(order)

        can_match = False
        
        if best_price is not None:
            if order.side == Side.BUY:
                other_side = Side.SELL
                if order.price >= best_price:
                    can_match = True
            else:
                other_side = Side.BUY
                if order.price <= best_price:
                    can_match = True

        if can_match:
            self.match_order(order, best_price, other_side)

        if order.remaining_quantity > 0:
            self.add_order_to_book(order)

        return order
    