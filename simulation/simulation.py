from exchange.exchange import Exchange
from exchange.market_state import MarketState
from traders.market_maker import MarketMaker

from exchange.order import Order
from exchange.enums import Side, OrderType, Event

from company.company import Company
from company.news_event import generate_news_event, apply_news_event
from company.social_event import generate_social_event, apply_social_event
from company.economic_event import generate_economic_event, apply_economic_event
from simulation.clock import SimClock, MINUTES_PER_DAY

import random
import heapq
import time
from itertools import count


class Simulation:
    def __init__(
        self,
        exchange: Exchange,
        traders: list,
        company: Company = None,
        days: int = 5,
        companies: dict = None,
        verbose=False,
        fee_rate=0.001,
        playback_delay_sec=0.0,
        sample_every_minutes=1,
    ):
        self.exchange = exchange
        self.exchange.fee_rate = fee_rate

        self.traders = traders
        self.trader_map = {trader.trader_id: trader for trader in traders}

        if companies is not None:
            self.companies = dict(companies)
        elif company is not None:
            self.companies = {company.symbol: company}
        else:
            raise ValueError("Provide company= or companies=")

        self.company = next(iter(self.companies.values()))
        self.primary_symbol = self.company.symbol

        for sym, comp in self.companies.items():
            self.exchange.list_symbol(comp.symbol)
            # Ensure dict key matches company.symbol
            if sym != comp.symbol:
                self.companies[comp.symbol] = comp

        for trader in self.traders:
            if not getattr(trader, "symbol", None):
                trader.symbol = self.primary_symbol

        self.days = int(days)
        self.total_minutes = SimClock.total_minutes(self.days)
        self.ticks = self.total_minutes  # alias for compatibility
        self.current_tick = 0
        self.clock = SimClock(0)

        self.verbose = verbose
        self.fee_rate = fee_rate
        self.total_fees = 0.0
        self.playback_delay_sec = playback_delay_sec
        self.sample_every_minutes = max(1, int(sample_every_minutes))

        self.bid_data = []
        self.ask_data = []
        self.mid_data = []
        self.spread_data = []
        self.fundamental_price_data = []
        self.volume_data = []
        self.last_trade_price_data = []

        self.revenue_data = []
        self.earnings_data = []
        self.book_value_data = []
        self.company_cash_data = []
        self.debt_data = []

        self.fundamental_ticks = []
        self.time_hours = []
        self.time_days = []
        self.time_labels = []

        self.event_queue = []
        self.event_counter = count()
        self.previous_tick = 0

        # Cadences in trading minutes — sparse enough for multi-week stability
        self.company_update_interval = MINUTES_PER_DAY          # once per day
        self.sentiment_update_interval = 15                     # ~every 15 min
        self.news_interval = MINUTES_PER_DAY                    # ~1 news/day
        self.social_interval = MINUTES_PER_DAY // 2             # ~2 social/day
        self.economic_interval = MINUTES_PER_DAY * 5            # ~weekly macro
        self.event_retention_ticks = MINUTES_PER_DAY            # keep ~1 day of headlines

        self.next_company_update = self.company_update_interval - 1  # near close of day 1
        self.next_sentiment_update = self.sentiment_update_interval
        self.next_news_event = random.randint(60, max(61, self.news_interval))
        self.next_social_event = random.randint(30, max(31, self.social_interval))
        self.next_economic_event = random.randint(120, max(121, self.economic_interval))

        self.recent_events = []
        self.event_history = []
        self._last_sample_minute = -1

    def _book(self, symbol=None):
        return self.exchange.get_book(symbol or self.primary_symbol)

    def _company_for(self, symbol=None):
        symbol = symbol or self.primary_symbol
        return self.companies[symbol]

    def _refund_order(self, order):
        trader = self.trader_map.get(order.trader_id)
        if trader is None:
            return

        if order.side == Side.BUY:
            if order.reserved_cash > 0:
                trader.money += order.reserved_cash
                order.reserved_cash = 0.0
        else:
            if order.reserved_shares > 0:
                trader.shares += order.reserved_shares
                order.reserved_shares = 0

    def build_market_state(self, symbol=None):
        symbol = symbol or self.primary_symbol
        book = self._book(symbol)
        company = self._company_for(symbol)
        self.clock.advance_to(self.current_tick)

        return MarketState(
            best_bid=book.get_best_bid(),
            best_ask=book.get_best_ask(),
            last_trade_price=book.get_last_trade_price(),
            spread=book.get_spread(),
            recent_prices=book.recent_prices,
            current_tick=self.current_tick,
            fundamental_price=company.fundamental_value,
            volume=book.current_volume,
            company=company,
            recent_events=list(self.recent_events),
            clock=SimClock(self.current_tick),
            time_label=self.clock.label(),
            symbol=symbol,
        )

    def process_trade(self, trade):
        buyer = self.trader_map[trade.buy_trader_id]
        seller = self.trader_map[trade.sell_trader_id]

        value = trade.price * trade.quantity
        fee = value * self.fee_rate

        buyer.money += trade.buyer_reservation_release - value
        buyer.shares += trade.quantity
        buyer.money -= fee

        seller.money += value - fee
        self.total_fees += fee * 2

        symbol = trade.symbol or self.primary_symbol
        self._company_for(symbol).update_market_stats(trade.price)

    def submit_action(self, trader, decision, current_tick):
        symbol = getattr(trader, "symbol", self.primary_symbol)
        book = self._book(symbol)

        order = Order(trader.trader_id, decision.side, decision.price, decision.quantity, decision.type)
        order.placed_tick = current_tick
        order.expiration_tick = current_tick + trader.order_ttl
        order.symbol = symbol

        if decision.type == OrderType.MARKET and decision.side == Side.BUY:
            ask = book.get_best_ask()
            if ask is None:
                return
            order.price = ask * 1.05
        elif decision.type == OrderType.MARKET and decision.side == Side.SELL:
            bid = book.get_best_bid()
            if bid is None:
                return
            order.price = bid

        if decision.side == Side.BUY:
            reserved = order.price * order.quantity * (1.0 + self.fee_rate)
            if trader.money < reserved:
                return
            trader.money -= reserved
            order.reserved_cash = reserved
        else:
            if trader.shares < order.quantity:
                return
            trader.shares -= order.quantity
            order.reserved_shares = order.quantity

        trades, cancelled = self.exchange.submit_order(order, current_tick, symbol=symbol)

        for trade in trades:
            self.process_trade(trade)

        for cancelled_order in cancelled:
            self._refund_order(cancelled_order)

        if self.verbose:
            print(
                f"{self.clock.label()}: "
                f"{trader.name}: "
                f"{decision.side.name} "
                f"{decision.quantity}"
                f" @ {decision.price} [{symbol}]"
            )

    def initialize_events(self):
        self.event_queue.clear()
        self.event_counter = count()
        self.total_fees = 0.0
        self.current_tick = 0
        self.clock.advance_to(0)
        self._last_sample_minute = -1

        for company in self.companies.values():
            company.sentiment.set(0.0)

        self.recent_events.clear()
        self.event_history.clear()

        self.next_company_update = self.company_update_interval - 1
        self.next_sentiment_update = self.sentiment_update_interval
        self.next_news_event = random.randint(60, max(61, self.news_interval))
        self.next_social_event = random.randint(30, max(31, self.social_interval))
        self.next_economic_event = random.randint(120, max(121, self.economic_interval))

        for trader in self.traders:
            first_tick = random.randint(0, 5)
            heapq.heappush(
                self.event_queue,
                Event(first_tick, next(self.event_counter), trader),
            )

    def _prune_recent_events(self):
        cutoff = self.current_tick - self.event_retention_ticks
        self.recent_events = [e for e in self.recent_events if e.tick >= cutoff]

    def _fire_market_event(self, event, company=None):
        company = company or self.company
        if event.source == "news":
            apply_news_event(company, event)
        elif event.source == "social":
            apply_social_event(company, event)
        elif event.source == "economic":
            apply_economic_event(company, event)

        self.recent_events.append(event)
        self.event_history.append(event)
        self._prune_recent_events()

        if self.verbose:
            print(f"{self.clock.label()}: [{event.source}] {event.headline} (mag={event.magnitude:.2f})")

    def _process_scheduled_updates(self):
        while self.current_tick >= self.next_company_update:
            for company in self.companies.values():
                company.update()
            self.next_company_update += self.company_update_interval

        while self.current_tick >= self.next_sentiment_update:
            for company in self.companies.values():
                company.sentiment.update()
            self.next_sentiment_update += self.sentiment_update_interval

        while self.current_tick >= self.next_news_event:
            for company in self.companies.values():
                event = generate_news_event(self.current_tick, company.name)
                self._fire_market_event(event, company)
            self.next_news_event += random.randint(
                max(1, self.news_interval // 2),
                self.news_interval * 2,
            )

        while self.current_tick >= self.next_social_event:
            for company in self.companies.values():
                event = generate_social_event(self.current_tick, company.name)
                self._fire_market_event(event, company)
            self.next_social_event += random.randint(
                max(1, self.social_interval // 2),
                self.social_interval * 2,
            )

        while self.current_tick >= self.next_economic_event:
            event = generate_economic_event(self.current_tick)
            for company in self.companies.values():
                self._fire_market_event(event, company)
            self.next_economic_event += random.randint(
                max(1, self.economic_interval // 2),
                self.economic_interval * 2,
            )

    def _record_sample(self):
        if self.current_tick - self._last_sample_minute < self.sample_every_minutes:
            if not self.clock.is_end_of_day:
                return
        self._last_sample_minute = self.current_tick

        market_state = self.build_market_state()
        if market_state.best_bid is not None and market_state.best_ask is not None:
            mid = (market_state.best_bid + market_state.best_ask) / 2
        else:
            mid = None

        self.bid_data.append(market_state.best_bid)
        self.ask_data.append(market_state.best_ask)
        self.mid_data.append(mid)
        self.spread_data.append(market_state.spread)
        self.fundamental_price_data.append(market_state.fundamental_price)
        self.fundamental_ticks.append(self.current_tick)
        self.time_hours.append(self.clock.to_hours())
        self.time_days.append(self.clock.to_days())
        self.time_labels.append(self.clock.label())
        self.volume_data.append(market_state.volume)
        self.revenue_data.append(self.company.revenue)
        self.earnings_data.append(self.company.earnings)
        self.book_value_data.append(self.company.book_value)
        self.company_cash_data.append(self.company.money)
        self.debt_data.append(self.company.debt)
        self.last_trade_price_data.append(market_state.last_trade_price)

    def process_event(self, event):
        self.current_tick = event.tick
        self.clock.advance_to(self.current_tick)

        self._process_scheduled_updates()

        trader = event.trader
        symbol = getattr(trader, "symbol", self.primary_symbol)

        if isinstance(trader, MarketMaker) and trader.should_refresh_quotes(self.current_tick):
            cancelled = self.exchange.cancel_trader_orders(trader.trader_id, symbol=symbol)
            for order in cancelled:
                self._refund_order(order)

        market_state = self.build_market_state(symbol)
        actions = trader.decide_action(market_state)

        if actions is not None:
            if not isinstance(actions, list):
                actions = [actions]
            for action in actions:
                self.submit_action(trader, action, self.current_tick)

        wait = max(1, int(random.expovariate(1 / max(trader.average_wait, 1))))
        heapq.heappush(
            self.event_queue,
            Event(self.current_tick + wait, next(self.event_counter), trader),
        )

        expired = self.exchange.cancel_expired_orders(self.current_tick)
        for order in expired:
            self._refund_order(order)

        self._record_sample()

        if self.playback_delay_sec > 0:
            time.sleep(self.playback_delay_sec)

    def run(self):
        self.initialize_events()

        while self.event_queue:
            event = heapq.heappop(self.event_queue)
            if event.tick > self.total_minutes:
                break
            self.process_event(event)

        return (
            self.bid_data,
            self.ask_data,
            self.mid_data,
            self.fundamental_price_data,
            self.spread_data,
            self.volume_data,
            self.last_trade_price_data,
            self.fundamental_ticks,
            self.revenue_data,
            self.earnings_data,
            self.book_value_data,
            self.company_cash_data,
            self.debt_data,
        )

    def reset(self):
        self.bid_data.clear()
        self.ask_data.clear()
        self.mid_data.clear()
        self.spread_data.clear()
        self.fundamental_price_data.clear()
        self.volume_data.clear()
        self.last_trade_price_data.clear()
        self.revenue_data.clear()
        self.earnings_data.clear()
        self.book_value_data.clear()
        self.company_cash_data.clear()
        self.debt_data.clear()
        self.fundamental_ticks.clear()
        self.time_hours.clear()
        self.time_days.clear()
        self.time_labels.clear()

        self.event_queue.clear()
        self.event_counter = count()
        self.current_tick = 0
        self.previous_tick = 0
        self.total_fees = 0.0
        self.clock.advance_to(0)
        self._last_sample_minute = -1

        self.recent_events.clear()
        self.event_history.clear()
        self.exchange.clear()

        self.next_company_update = self.company_update_interval - 1
        self.next_sentiment_update = self.sentiment_update_interval
        self.next_news_event = random.randint(60, max(61, self.news_interval))
        self.next_social_event = random.randint(30, max(31, self.social_interval))
        self.next_economic_event = random.randint(120, max(121, self.economic_interval))
