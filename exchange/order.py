class Order:
    def __init__(self, trader_id, side, price, quantity, timestamp, order_type):
        self.trader_id = trader_id
        self.side = side
        self.price = price
        self.quantity = quantity
        self.remaining_quantity = quantity
        self.timestamp = timestamp
        self.type = order_type
        self.status = "NEW"
        self.id = None

