import time
from exchange.enums import OrderStatus

class Order:
    def __init__(self, trader_id, side, price, quantity, order_type):
        self.trader_id = trader_id

        self.side = side
        self.price = price
        self.quantity = quantity

        self.remaining_quantity = quantity

        self.timestamp = time.time()

        self.type = order_type

        self.status = OrderStatus.NEW

        self.id = None

        self.placed_tick = None
        self.expiration_tick = None

    def __str__(self):
        return (
            f"Order: "
            f"{self.trader_id}, "
            f"{self.side.name}, "
            f"{self.quantity}, "
            f"@ {self.price}, "
            f"{self.type.name}, "
            f"{self.status.name}"
        )

    def __repr__(self):
        return (
            f"Order("
            f"{self.side.name}, "
            f"{self.remaining_quantity}/"
            f"{self.quantity}"
            f" @ {self.price}, "
            f"{self.type.name}, "
            f"id={self.id}, "
            f"expires={self.expiration_tick})"
        )