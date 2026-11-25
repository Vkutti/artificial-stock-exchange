class Trade:
    def __init__(
        self,
        buy_trader_id,
        sell_trader_id,
        price,
        quantity,
        timestamp,
        tick,
        buyer_reservation_release=0.0,
        seller_shares_release=0,
        symbol=None,
    ):
        self.buy_trader_id = buy_trader_id
        self.sell_trader_id = sell_trader_id
        self.price = price
        self.quantity = quantity
        self.timestamp = timestamp
        self.tick = tick
        self.buyer_reservation_release = buyer_reservation_release
        self.seller_shares_release = seller_shares_release
        self.symbol = symbol

    def __repr__(self):
        return (
            f"Trade("
            f"{self.symbol} "
            f"{self.buy_trader_id} -> "
            f"{self.sell_trader_id}, "
            f"{self.quantity}@{self.price})"
        )
