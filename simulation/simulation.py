from exchange.exchange import Exchange
from exchange.market_state import MarketState, PublicHeadline
from traders.market_maker import MarketMaker

from exchange.order import Order
from exchange.enums import Side, OrderType
from exchange.ticks import round_to_tick

from company.company import Company
from company.news_event import generate_news_event, apply_news_event
from company.social_event import generate_social_event, apply_social_event
from company.economic_event import generate_economic_event, apply_economic_event
from company.sector_event import generate_sector_event, apply_sector_event
from company.liquidity_event import (
    generate_liquidity_event,
    stress_multiplier_from_event,
    duration_from_event,
)
from company.economy import Economy
from simulation.clock import SimClock, MINUTES_PER_DAY
from simulation.events import Event

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
        economy: Economy = None,
        enable_auctions=True,
        enable_session_prints=None,
        enable_circuit_breakers=True,
        seed=None,
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
        self.economy = economy or Economy()

        for sym, comp in self.companies.items():
            self.exchange.list_symbol(comp.symbol)
            if sym != comp.symbol:
                self.companies[comp.symbol] = comp
            comp.apply_economy(self.economy)

        self.seed = seed
        for trader in self.traders:
            if not getattr(trader, "symbol", None):
                trader.symbol = self.primary_symbol
            if not hasattr(trader, "fv_bias"):
                trader.fv_bias = random.gauss(0, 0.02)
            if not hasattr(trader, "fv_noise"):
                trader.fv_noise = 0.0

        self.days = int(days)
        self.total_minutes = SimClock.total_minutes(self.days)
        self.ticks = self.total_minutes
        self.current_tick = 0
        self.clock = SimClock(0)

        self.verbose = verbose
        self.fee_rate = fee_rate
        self.total_fees = 0.0
        self.playback_delay_sec = playback_delay_sec
        self.sample_every_minutes = max(1, int(sample_every_minutes))
        if enable_session_prints is None:
            enable_session_prints = enable_auctions
        self.enable_session_prints = enable_session_prints
        self.enable_auctions = enable_session_prints
        self.enable_circuit_breakers = enable_circuit_breakers

        self.bid_data = []
        self.ask_data = []
        self.mid_data = []
        self.spread_data = []
        self.fundamental_price_data = []
        self.true_fundamental_data = []
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

        self.company_update_interval = MINUTES_PER_DAY
        self.sentiment_update_interval = 15
        self.news_interval = (MINUTES_PER_DAY * 3) // 2
        self.social_interval = MINUTES_PER_DAY // 2
        self.economic_interval = MINUTES_PER_DAY * 5
        self.sector_interval = MINUTES_PER_DAY * 4
        self.liquidity_interval = MINUTES_PER_DAY * 3
        self.event_retention_ticks = MINUTES_PER_DAY
        self.flow_update_interval = 60

        self.next_company_update = self.company_update_interval - 1
        self.next_sentiment_update = self.sentiment_update_interval
        self.next_news_event = random.randint(60, max(61, self.news_interval))
        self.next_social_event = random.randint(30, max(31, self.social_interval))
        self.next_economic_event = random.randint(120, max(121, self.economic_interval))
        self.next_sector_event = random.randint(90, max(91, self.sector_interval))
        self.next_liquidity_event = random.randint(80, max(81, self.liquidity_interval))
        self.next_flow_update = self.flow_update_interval

        self.recent_events = []
        self.event_history = []
        self._last_sample_minute = -1

        self.prior_close = {s: c.fundamental_value for s, c in self.companies.items()}
        self.breaker_ref = {s: c.fundamental_value for s, c in self.companies.items()}
        self.halted_until = {s: -1 for s in self.companies}
        self.halt_cooldown_until = {s: -1 for s in self.companies}
        self.halt_counts = {s: 0 for s in self.companies}
        self.session_prints = []
        self.auction_prints = self.session_prints
        self.breaker_band = 0.07
        self.breaker_halt_minutes = 15
        self.breaker_cooldown_minutes = 30
        self.breaker_ref_alpha = 0.05
        self._last_print_day = -1
        self._close_print_done_day = -1
        self.liquidity_stress = 1.0
        self.liquidity_stress_until = -1
        self.symbol_series = {
            s: {"bid": [], "ask": [], "mid": [], "last": [], "fv": [], "spread": []}
            for s in self.companies
        }

    def _book(self, symbol=None):
        return self.exchange.get_book(symbol or self.primary_symbol)

    def _company_for(self, symbol=None):
        return self.companies[symbol or self.primary_symbol]

    def _session_phase(self):
        sm = self.clock.session_minute
        if self.enable_session_prints and sm == 0:
            return "open_print"
        if self.enable_session_prints and sm == MINUTES_PER_DAY - 1:
            return "close_print"
        return "continuous"

    def _is_halted(self, symbol):
        return self.current_tick < self.halted_until.get(symbol, -1)

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

    def _refund_all_resting(self):
        for trader in self.traders:
            for order in self.exchange.cancel_trader_orders(trader.trader_id):
                self._refund_order(order)

    def _public_events_for(self, symbol):
        company = self._company_for(symbol)
        out = []
        for e in self.recent_events:
            if e.source == "sector":
                if e.sector != company.industry:
                    continue
            elif e.source == "liquidity":
                pass
            elif e.source == "economic":
                pass
            elif e.symbol is not None and e.symbol != symbol:
                continue
            out.append(
                PublicHeadline(
                    tick=e.tick,
                    kind=e.kind,
                    source=e.source,
                    headline=e.headline,
                    symbol=e.symbol,
                    sign=e.sign,
                    intensity=e.intensity,
                    sector=getattr(e, "sector", None),
                )
            )
        return out

    def _current_liquidity_stress(self):
        if self.current_tick >= self.liquidity_stress_until:
            self.liquidity_stress = 1.0
        return self.liquidity_stress

    def _step_fv_noise(self, trader):
        if trader is None:
            return 0.0
        noise = getattr(trader, "fv_noise", 0.0)
        noise += 0.02 * (0.0 - noise) + random.gauss(0, 0.0015)
        noise = max(-0.05, min(0.05, noise))
        trader.fv_noise = noise
        return noise

    def _estimate_fv(self, company, trader=None):
        bias = getattr(trader, "fv_bias", 0.0) if trader is not None else 0.0
        noise = self._step_fv_noise(trader) if trader is not None else 0.0
        return max(0.01, company.fundamental_value * (1.0 + bias + noise))

    def build_market_state(self, symbol=None, trader=None):
        symbol = symbol or self.primary_symbol
        book = self._book(symbol)
        company = self._company_for(symbol)
        self.clock.advance_to(self.current_tick)
        hist = company.sentiment.history[-50:]

        bid = book.get_best_bid()
        ask = book.get_best_ask()
        imbalance = 0.0
        if bid is not None and ask is not None:
            buy_depth = sum(o.remaining_quantity for o in book.order_book[Side.BUY].get(bid, []))
            sell_depth = sum(o.remaining_quantity for o in book.order_book[Side.SELL].get(ask, []))
            denom = buy_depth + sell_depth
            imbalance = (buy_depth - sell_depth) / denom if denom else 0.0

        return MarketState(
            best_bid=bid,
            best_ask=ask,
            last_trade_price=book.get_last_trade_price(),
            spread=book.get_spread(),
            recent_prices=book.recent_prices,
            current_tick=self.current_tick,
            fundamental_price=self._estimate_fv(company, trader),
            volume=book.current_volume,
            company=None,
            recent_events=self._public_events_for(symbol),
            clock=SimClock(self.current_tick),
            time_label=self.clock.label(),
            symbol=symbol,
            sentiment_value=company.sentiment.value,
            sentiment_history=hist,
            imbalance=imbalance,
            halted=self._is_halted(symbol),
            session_phase=self._session_phase(),
            flow_multiplier=self.economy.flow_multiplier,
            risk_free_rate=self.economy.risk_free_rate,
            bid_depth=book.get_depth(Side.BUY, levels=5),
            ask_depth=book.get_depth(Side.SELL, levels=5),
            liquidity_stress=self._current_liquidity_stress(),
            sector=company.industry,
        )

    def process_trade(self, trade):
        buyer = self.trader_map[trade.buy_trader_id]
        seller = self.trader_map[trade.sell_trader_id]

        value = trade.price * trade.quantity
        fee = value * self.fee_rate
        cost = value + fee

        release = trade.buyer_reservation_release
        if release + 1e-9 < cost:
            raise RuntimeError(
                f"under-collateralized buy: release={release:.6f} cost={cost:.6f}"
            )

        buyer.money += release - cost
        buyer.shares += trade.quantity
        if buyer.money < -1e-6:
            raise RuntimeError(f"buyer cash negative: {buyer.money}")

        seller.money += value - fee
        self.total_fees += fee * 2

        symbol = trade.symbol or self.primary_symbol
        self._company_for(symbol).update_market_stats(trade.price)
        self._update_breaker_ref(symbol, trade.price)
        self._maybe_halt(symbol, trade.price)

    def _update_breaker_ref(self, symbol, price):
        prev = self.breaker_ref.get(symbol, price)
        a = self.breaker_ref_alpha
        self.breaker_ref[symbol] = (1.0 - a) * prev + a * price

    def _maybe_halt(self, symbol, price):
        if not self.enable_circuit_breakers:
            return
        if self._is_halted(symbol):
            return
        if self.current_tick < self.halt_cooldown_until.get(symbol, -1):
            return
        ref = self.breaker_ref.get(symbol) or price
        if ref <= 0:
            return
        move = abs(price / ref - 1.0)
        if move >= self.breaker_band:
            self.halted_until[symbol] = self.current_tick + self.breaker_halt_minutes
            self.halt_cooldown_until[symbol] = (
                self.halted_until[symbol] + self.breaker_cooldown_minutes
            )
            self.halt_counts[symbol] = self.halt_counts.get(symbol, 0) + 1
            self.breaker_ref[symbol] = price
            cancelled = []
            for trader in self.traders:
                if getattr(trader, "symbol", None) == symbol:
                    cancelled.extend(
                        self.exchange.cancel_trader_orders(trader.trader_id, symbol=symbol)
                    )
            for order in cancelled:
                self._refund_order(order)

    def submit_action(self, trader, decision, current_tick):
        symbol = getattr(trader, "symbol", self.primary_symbol)
        if self._is_halted(symbol):
            return
        if self._session_phase() != "continuous" and decision.type == OrderType.MARKET:
            return

        book = self._book(symbol)
        tick_size = self.exchange.tick_size

        order = Order(trader.trader_id, decision.side, decision.price, decision.quantity, decision.type)
        order.placed_tick = current_tick
        order.timestamp = current_tick
        order.expiration_tick = current_tick + trader.order_ttl
        order.symbol = symbol

        if decision.type == OrderType.MARKET and decision.side == Side.BUY:
            ask = book.get_best_ask()
            if ask is None:
                return
            order.price = round_to_tick(ask * 1.05, tick_size)
        elif decision.type == OrderType.MARKET and decision.side == Side.SELL:
            bid = book.get_best_bid()
            if bid is None:
                return
            order.price = tick_size
        else:
            order.price = round_to_tick(decision.price, tick_size)

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
                f"{self.clock.label()}: {trader.name}: "
                f"{decision.side.name} {decision.quantity} @ {decision.price} [{symbol}]"
            )

    def initialize_events(self):
        self.event_queue.clear()
        self.event_counter = count()
        self.total_fees = 0.0
        self.current_tick = 0
        self.clock.advance_to(0)
        self._last_sample_minute = -1
        self._last_print_day = -1
        self._close_print_done_day = -1
        self.session_prints.clear()

        for company in self.companies.values():
            company.sentiment.set(0.0)
            company.apply_economy(self.economy)

        self.prior_close = {s: c.fundamental_value for s, c in self.companies.items()}
        self.breaker_ref = {s: c.fundamental_value for s, c in self.companies.items()}
        self.halted_until = {s: -1 for s in self.companies}
        self.halt_cooldown_until = {s: -1 for s in self.companies}
        for series in self.symbol_series.values():
            for key in series:
                series[key].clear()

        self.recent_events.clear()
        self.event_history.clear()

        self.next_company_update = self.company_update_interval - 1
        self.next_sentiment_update = self.sentiment_update_interval
        self.next_news_event = random.randint(60, max(61, self.news_interval))
        self.next_social_event = random.randint(30, max(31, self.social_interval))
        self.next_economic_event = random.randint(120, max(121, self.economic_interval))
        self.next_sector_event = random.randint(90, max(91, self.sector_interval))
        self.next_liquidity_event = random.randint(80, max(81, self.liquidity_interval))
        self.next_flow_update = self.flow_update_interval
        self.liquidity_stress = 1.0
        self.liquidity_stress_until = -1

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
            if event.kind in ("rate_hike", "rate_cut", "inflation_spike"):
                self.economy.apply_rate_shock(event.magnitude)
                for c in self.companies.values():
                    c.apply_economy(self.economy)
        elif event.source == "sector":
            for c in self.companies.values():
                if c.industry == event.sector:
                    apply_sector_event(c, event)
        elif event.source == "liquidity":
            self.liquidity_stress = stress_multiplier_from_event(event)
            self.liquidity_stress_until = self.current_tick + duration_from_event(event)

        self.recent_events.append(event)
        self.event_history.append(event)
        self._prune_recent_events()

    def _run_auction(self, symbol, phase):
        book = self._book(symbol)
        company = self._company_for(symbol)
        trades, clearing, matched_qty = book.execute_midpoint_cross(
            self.current_tick, tick_size=self.exchange.tick_size
        )
        if trades:
            for trade in trades:
                trade.symbol = symbol
                cost = trade.price * trade.quantity * (1.0 + self.fee_rate)
                if trade.buyer_reservation_release + 1e-9 < cost:
                    buyer = self.trader_map.get(trade.buy_trader_id)
                    need = cost - trade.buyer_reservation_release
                    if buyer is not None and buyer.money + 1e-9 >= need:
                        buyer.money -= need
                        trade.buyer_reservation_release = cost
                self.exchange.trade_history.append(trade)
                self.process_trade(trade)
            price = clearing
        else:
            bid = book.get_best_bid()
            ask = book.get_best_ask()
            if bid is None and ask is None:
                price = company.fundamental_value
            elif bid is None:
                price = ask
            elif ask is None:
                price = bid
            else:
                price = 0.5 * (bid + ask)
            price = round_to_tick(price, self.exchange.tick_size)
            book.recent_prices.append(price)
            if len(book.recent_prices) > 1000:
                book.recent_prices.pop(0)
            matched_qty = 0

        company.update_market_stats(price)
        self._update_breaker_ref(symbol, price)
        self.session_prints.append(
            {
                "tick": self.current_tick,
                "symbol": symbol,
                "phase": phase,
                "price": price,
                "volume": matched_qty,
            }
        )
        if phase == "close":
            self.prior_close[symbol] = price
            self.breaker_ref[symbol] = price

    def _maybe_run_session_prints(self):
        if not self.enable_session_prints:
            return
        day = self.clock.day
        sm = self.clock.session_minute
        if sm == 0 and self._last_print_day != day:
            for symbol in self.companies:
                if not self._is_halted(symbol):
                    self._run_auction(symbol, "open")
            self._last_print_day = day
        if sm == MINUTES_PER_DAY - 1 and self._close_print_done_day != day:
            for symbol in self.companies:
                if not self._is_halted(symbol):
                    self._run_auction(symbol, "close")
            self._close_print_done_day = day

    def _maybe_run_auctions(self):
        self._maybe_run_session_prints()

    def _process_scheduled_updates(self):
        while self.current_tick >= self.next_company_update:
            for company in self.companies.values():
                company.apply_economy(self.economy)
                company.update()
            self.next_company_update += self.company_update_interval

        while self.current_tick >= self.next_sentiment_update:
            for company in self.companies.values():
                company.sentiment.update()
            self.next_sentiment_update += self.sentiment_update_interval

        while self.current_tick >= self.next_flow_update:
            self.economy.update_flow_regime()
            self.next_flow_update += self.flow_update_interval

        while self.current_tick >= self.next_news_event:
            for company in self.companies.values():
                event = generate_news_event(
                    self.current_tick, company.name, symbol=company.symbol
                )
                self._fire_market_event(event, company)
            self.next_news_event += random.randint(
                max(1, self.news_interval // 2),
                self.news_interval * 2,
            )

        while self.current_tick >= self.next_social_event:
            for company in self.companies.values():
                event = generate_social_event(
                    self.current_tick, company.name, symbol=company.symbol
                )
                self._fire_market_event(event, company)
            self.next_social_event += random.randint(
                max(1, self.social_interval // 2),
                self.social_interval * 2,
            )

        while self.current_tick >= self.next_economic_event:
            event = generate_economic_event(self.current_tick, symbol=None)
            for company in self.companies.values():
                apply_economic_event(company, event)
            if event.kind in ("rate_hike", "rate_cut", "inflation_spike"):
                self.economy.apply_rate_shock(event.magnitude)
                for c in self.companies.values():
                    c.apply_economy(self.economy)
            self.recent_events.append(event)
            self.event_history.append(event)
            self._prune_recent_events()
            self.next_economic_event += random.randint(
                max(1, self.economic_interval // 2),
                self.economic_interval * 2,
            )

        while self.current_tick >= self.next_sector_event:
            sectors = sorted({c.industry for c in self.companies.values()})
            sector_name = random.choice(sectors)
            event = generate_sector_event(self.current_tick, sector_name)
            self._fire_market_event(event)
            self.next_sector_event += random.randint(
                max(1, self.sector_interval // 2),
                self.sector_interval * 2,
            )

        while self.current_tick >= self.next_liquidity_event:
            event = generate_liquidity_event(self.current_tick)
            self._fire_market_event(event)
            self.next_liquidity_event += random.randint(
                max(1, self.liquidity_interval // 2),
                self.liquidity_interval * 2,
            )

        self._current_liquidity_stress()
        self._maybe_run_session_prints()

    def _record_sample(self):
        if self.current_tick - self._last_sample_minute < self.sample_every_minutes:
            if not self.clock.is_end_of_day:
                return
        self._last_sample_minute = self.current_tick

        self.fundamental_ticks.append(self.current_tick)
        self.time_hours.append(self.clock.to_hours())
        self.time_days.append(self.clock.to_days())
        self.time_labels.append(self.clock.label())

        for symbol, company in self.companies.items():
            state = self.build_market_state(symbol)
            if state.best_bid is not None and state.best_ask is not None:
                mid = (state.best_bid + state.best_ask) / 2
            else:
                mid = None
            series = self.symbol_series[symbol]
            series["bid"].append(state.best_bid)
            series["ask"].append(state.best_ask)
            series["mid"].append(mid)
            series["last"].append(state.last_trade_price)
            series["fv"].append(company.fundamental_value)
            series["spread"].append(state.spread)

        primary = self.symbol_series[self.primary_symbol]
        self.bid_data.append(primary["bid"][-1])
        self.ask_data.append(primary["ask"][-1])
        self.mid_data.append(primary["mid"][-1])
        self.spread_data.append(primary["spread"][-1])
        self.fundamental_price_data.append(primary["fv"][-1])
        self.true_fundamental_data.append(primary["fv"][-1])
        self.volume_data.append(self._book(self.primary_symbol).current_volume)
        self.revenue_data.append(self.company.revenue)
        self.earnings_data.append(self.company.earnings)
        self.book_value_data.append(self.company.book_value)
        self.company_cash_data.append(self.company.money)
        self.debt_data.append(self.company.debt)
        self.last_trade_price_data.append(primary["last"][-1])

    def process_event(self, event):
        self.current_tick = event.tick
        self.clock.advance_to(self.current_tick)

        self._process_scheduled_updates()

        trader = event.trader
        symbol = getattr(trader, "symbol", self.primary_symbol)

        if self._is_halted(symbol):
            wait = max(1, int(random.expovariate(1 / max(trader.average_wait, 1))))
            heapq.heappush(
                self.event_queue,
                Event(self.current_tick + wait, next(self.event_counter), trader),
            )
            self._record_sample()
            return

        if isinstance(trader, MarketMaker) and trader.should_refresh_quotes(self.current_tick):
            cancelled = self.exchange.cancel_trader_orders(trader.trader_id, symbol=symbol)
            for order in cancelled:
                self._refund_order(order)

        market_state = self.build_market_state(symbol, trader=trader)
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

        self._refund_all_resting()

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
        self._refund_all_resting()
        self.bid_data.clear()
        self.ask_data.clear()
        self.mid_data.clear()
        self.spread_data.clear()
        self.fundamental_price_data.clear()
        self.true_fundamental_data.clear()
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
        self.session_prints.clear()
        for series in self.symbol_series.values():
            for key in series:
                series[key].clear()

        self.event_queue.clear()
        self.event_counter = count()
        self.current_tick = 0
        self.previous_tick = 0
        self.total_fees = 0.0
        self.clock.advance_to(0)
        self._last_sample_minute = -1
        self._last_print_day = -1
        self._close_print_done_day = -1

        self.recent_events.clear()
        self.event_history.clear()
        self.exchange.clear()
        self.halted_until = {s: -1 for s in self.companies}
        self.halt_cooldown_until = {s: -1 for s in self.companies}
        self.breaker_ref = {s: c.fundamental_value for s, c in self.companies.items()}

        self.next_company_update = self.company_update_interval - 1
        self.next_sentiment_update = self.sentiment_update_interval
        self.next_news_event = random.randint(60, max(61, self.news_interval))
        self.next_social_event = random.randint(30, max(31, self.social_interval))
        self.next_economic_event = random.randint(120, max(121, self.economic_interval))
        self.next_sector_event = random.randint(90, max(91, self.sector_interval))
        self.next_liquidity_event = random.randint(80, max(81, self.liquidity_interval))
        self.next_flow_update = self.flow_update_interval
        self.liquidity_stress = 1.0
        self.liquidity_stress_until = -1
