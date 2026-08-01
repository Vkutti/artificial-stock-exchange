class Trade:
    def __init__(self, buy_trader_id, sell_trader_id, price, quantity, timestamp):
        self.buy_trader_id = buy_trader_id
        self.sell_trader_id = sell_trader_id
        self.price = price
        self.quantity = quantity
        self.timestamp = timestamp

    def __repr__(self):
        return (
            f"Trade("
            f"{self.buy_trader_id} -> "
            f"{self.sell_trader_id}, "
            f"{self.quantity}@{self.price})"
        )