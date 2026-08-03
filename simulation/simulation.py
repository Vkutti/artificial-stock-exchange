from exchange.exchange import Exchange
from exchange.market_state import MarketState
from traders.random_trader import RandomTrader
from traders.market_maker import MarketMaker
from traders.momentum_trader import MomentumTrader
from traders.fair_value_trader import FairValueTrader
from exchange.order import Order
from exchange.enums import Side

import random

class Simulation:
    def __init__(self, exchange: Exchange, traders: list[RandomTrader | MarketMaker | FairValueTrader | MomentumTrader], ticks):
        self.exchange = exchange

        self.traders = traders

        self.trader_map = {trader.trader_id: trader for trader in traders}

        self.ticks = ticks

        self.current_tick = 0

        self.bid_data = []
        self.ask_data = []
        self.mid_data = []
        self.spread_data = []
        self.fundamental_price_data = []
        self.volume_data = []

        self.fundamental_price = 100

    def build_market_state(self):
        return MarketState(
            best_bid=self.exchange.get_best_bid(),
            best_ask=self.exchange.get_best_ask(),
            last_trade_price=self.exchange.get_last_trade_price(),
            spread=self.exchange.get_spread(),
            recent_prices=self.exchange.recent_prices,
            current_tick=self.current_tick,
            fundamental_price=self.fundamental_price, 
            volume=self.exchange.current_volume)

    def process_trade(self, trade):
        buyer = self.trader_map[trade.buy_trader_id]

        seller = self.trader_map[trade.sell_trader_id]

        value = (trade.price * trade.quantity)

        buyer.shares += trade.quantity

        seller.money += value

    def submit_action(self, trader, decision, current_tick):
        order = Order(trader.trader_id, decision.side, decision.price, decision.quantity, decision.type)

        order.placed_tick = current_tick

        order.expiration_tick = (current_tick + trader.order_ttl)

        if decision.side == Side.BUY:
            cost = (decision.price * decision.quantity)

            if trader.money < cost:
                return

            trader.money -= cost
        else:
            if trader.shares < decision.quantity:
                return
            
            trader.shares -= decision.quantity

        trades = self.exchange.submit_order(order)

        for trade in trades:
            self.process_trade(trade)

        print(
            f"Tick {current_tick}: "
            f"{trader.name}: "
            f"{decision.side.name} "
            f"{decision.quantity}"
            f" @ {decision.price}"
        )

    def step(self, current_tick):
        self.current_tick = current_tick

        active_traders = self.traders.copy()
        random.shuffle(active_traders)

        for trader in active_traders:
            if current_tick < trader.next_action_tick:
                continue

            market_state = self.build_market_state()

            actions = trader.decide_action(market_state)

            if actions is None:

                trader.next_action_tick = (current_tick + max(1, int(random.expovariate(1 / trader.average_wait))))
                continue

            if not isinstance(actions, list):
                actions = [actions]

            for action in actions:
                self.submit_action(trader, action, current_tick)

            trader.next_action_tick = (current_tick + max(1, int(random.expovariate(1 / trader.average_wait))))

        expired = (self.exchange.cancel_expired_orders(current_tick))

        for order in expired:
            trader = self.trader_map[order.trader_id]

            if order.side == Side.BUY:
                trader.money += (order.price * order.remaining_quantity)
            else:
                trader.shares += (order.remaining_quantity)

        drift = 0.002 * (100 - self.fundamental_price)
        noise = random.gauss(0, 0.05)

        self.fundamental_price += drift + noise

    def run(self):
        for tick in range(self.ticks):
            self.step(tick)

            market_state = (self.build_market_state())

            self.bid_data.append(market_state.best_bid)

            self.ask_data.append(market_state.best_ask)

            if (market_state.best_bid is not None and market_state.best_ask is not None):
                mid = (market_state.best_bid + market_state.best_ask) / 2
            else:
                mid = None

            self.mid_data.append(mid)

            self.spread_data.append(market_state.spread)
            self.fundamental_price_data.append(market_state.fundamental_price)
            self.volume_data.append(market_state.volume)


        return (self.bid_data, self.ask_data, self.mid_data, self.fundamental_price_data, self.spread_data, self.volume_data)

    def reset(self):
        self.bid_data.clear()

        self.ask_data.clear()

        self.mid_data.clear()