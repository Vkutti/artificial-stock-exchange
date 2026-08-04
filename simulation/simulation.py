from exchange.exchange import Exchange
from exchange.market_state import MarketState
from traders.random_trader import RandomTrader
from traders.market_maker import MarketMaker
from traders.momentum_trader import MomentumTrader
from traders.fair_value_trader import FairValueTrader
from exchange.order import Order
from exchange.enums import Side

from exchange.enums import Event

import random
import heapq
from itertools import count

import matplotlib.pyplot as plt
import numpy as np

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

        self.event_queue = []
        self.event_counter = count()

        self.previous_tick = 0
        
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
            reserved = order.price * order.quantity

            if trader.money < reserved:
                return

            trader.money -= reserved
            
        else:
            if trader.shares < order.quantity:
                return
            
            trader.shares -= order.quantity

        trades = self.exchange.submit_order(order)

        for trade in trades:
            self.process_trade(trade)

            if order.side == Side.BUY:
                reserved_cost = order.price * trade.quantity
                actual_cost = trade.price * trade.quantity

                trader.money += reserved_cost - actual_cost

        print(
            f"Tick {current_tick}: "
            f"{trader.name}: "
            f"{decision.side.name} "
            f"{decision.quantity}"
            f" @ {decision.price}"

           # f"Current Amount of Money: {trader.money}"
        )

    def initialize_events(self):
        self.event_queue.clear()
        self.event_counter = count()

        for trader in self.traders:
            first_tick = random.randint(0, 5)

            heapq.heappush(
                self.event_queue,
                Event(
                    first_tick,
                    next(self.event_counter),
                    trader
                )
            )

    def process_event(self, event):
        self.current_tick = event.tick

        trader = event.trader

        market_state = self.build_market_state()

        actions = trader.decide_action(market_state)

        if actions is not None:

            if not isinstance(actions, list):
                actions = [actions]

            for action in actions:
                self.submit_action(
                    trader,
                    action,
                    self.current_tick
                )

        wait = max(
            1,
            int(random.expovariate(1 / trader.average_wait))
        )

        heapq.heappush(
            self.event_queue,
            Event(
                self.current_tick + wait,
                next(self.event_counter),
                trader
            )
        )


        expired = self.exchange.cancel_expired_orders(
            self.current_tick
        )

        for order in expired:

            trader = self.trader_map[order.trader_id]

            if order.side == Side.BUY:
                trader.money += (
                    order.price *
                    order.remaining_quantity
                )

            else:
                trader.shares += order.remaining_quantity

        drift = 0.00005
        dt = self.current_tick - self.previous_tick

        self.previous_tick = self.current_tick

        noise = random.gauss(0, 0.02 * (dt ** 0.5))

        self.fundamental_price += drift * dt + noise

    def run(self):

        # plt.ion()

        # fig, ax = plt.subplots()

        # line, = ax.plot([], [])

        # ax.set_title("Mid Price")

        self.initialize_events()

        while self.event_queue:

            event = heapq.heappop(self.event_queue)

            if event.tick > self.ticks:
                break

            self.process_event(event)

            market_state = self.build_market_state()

            if (
                market_state.best_bid is not None
                and
                market_state.best_ask is not None
            ):
                mid = (
                    market_state.best_bid
                    +
                    market_state.best_ask
                ) / 2
            else:
                mid = None

            self.bid_data.append(
                market_state.best_bid
            )

            self.ask_data.append(
                market_state.best_ask
            )

            self.mid_data.append(mid)

            self.spread_data.append(
                market_state.spread
            )

            self.fundamental_price_data.append(
                market_state.fundamental_price
            )

            self.volume_data.append(
                market_state.volume
            )

            self.mid_data.append(mid)

        #     if len(self.mid_data) % 500 == 0:
        #         line.set_data(range(len(self.mid_data)), self.mid_data)
        #         ax.relim()
        #         ax.autoscale_view()

        #         plt.draw()
        #         plt.pause(0.001)

        # plt.ioff()
        # plt.show()

        return (
            self.bid_data,
            self.ask_data,
            self.mid_data,
            self.fundamental_price_data,
            self.spread_data,
            self.volume_data,
        )

    def reset(self):
        self.bid_data.clear()

        self.ask_data.clear()

        self.mid_data.clear()