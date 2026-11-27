from exchange.exchange import Exchange
from exchange.order import Order
from exchange.enums import Side, OrderType
from simulation.simulation import Simulation
from traders.market_maker import MarketMaker
from traders.random_trader import RandomTrader
from traders.mean_reversion_trader import MeanReversionTrader
from traders.breakout_trader import BreakoutTrader
from traders.attention_trader import AttentionTrader
from company.company import Company
from company.sector_event import generate_sector_event, apply_sector_event
from company.liquidity_event import generate_liquidity_event, stress_multiplier_from_event


def _co(name, industry, symbol):
    return Company(name, industry, 1e7, 2e6, 1e6, 3.6e6, 8e6, 1e6, 0.5, symbol=symbol)


def test_order_book_depth_levels():
    exchange = Exchange()
    exchange.list_symbol("ABC")
    book = exchange.get_book("ABC")
    for i, px in enumerate([99.0, 98.5, 98.0]):
        o = Order(f"b{i}", Side.BUY, px, 10 + i, OrderType.LIMIT)
        o.expiration_tick = 1000
        book.submit_order(o, 0)
    for i, px in enumerate([101.0, 101.5, 102.0]):
        o = Order(f"s{i}", Side.SELL, px, 8 + i, OrderType.LIMIT)
        o.expiration_tick = 1000
        book.submit_order(o, 0)
    bids = book.get_depth(Side.BUY, levels=2)
    asks = book.get_depth(Side.SELL, levels=2)
    assert bids[0][0] == 99.0
    assert asks[0][0] == 101.0
    assert len(bids) == 2
    assert len(asks) == 2


def test_clearing_cross_matches_volume():
    exchange = Exchange()
    exchange.list_symbol("ABC")
    book = exchange.get_book("ABC")

    buy = Order("b1", Side.BUY, 100.0, 20, OrderType.LIMIT)
    buy.expiration_tick = 1000
    buy.reserved_cash = 100.0 * 20 * 1.001
    sell = Order("s1", Side.SELL, 99.0, 15, OrderType.LIMIT)
    sell.expiration_tick = 1000
    sell.reserved_shares = 15
    book.add_order_to_book(buy)
    book.add_order_to_book(sell)

    price, vol = book.find_clearing_price(reference=100.0)
    assert price is not None
    assert vol == 15
    trades = book.execute_cross(price, 1, max_volume=vol)
    assert sum(t.quantity for t in trades) == 15
    assert book.get_best_bid() == 100.0
    assert buy.remaining_quantity == 5
    assert sell.remaining_quantity == 0


def test_auction_records_volume_when_book_crosses():
    company = _co("ABC Inc", "Technology", "ABC")
    mm = MarketMaker("mm", 200000, 5000, 0)
    mm.symbol = "ABC"
    sim = Simulation(Exchange(), [mm], company=company, days=1, enable_session_prints=True)
    book = sim._book("ABC")
    buy = Order(mm.trader_id, Side.BUY, 105.0, 10, OrderType.LIMIT)
    buy.expiration_tick = 1000
    buy.reserved_cash = 105.0 * 10 * 1.001
    mm.money -= buy.reserved_cash
    sell = Order("other", Side.SELL, 95.0, 10, OrderType.LIMIT)
    sell.expiration_tick = 1000
    sell.reserved_shares = 10
    book.add_order_to_book(buy)
    book.add_order_to_book(sell)

    class _S:
        trader_id = "other"
        money = 0.0
        shares = 0
        name = "other"
        symbol = "ABC"

    seller = _S()
    sim.trader_map[seller.trader_id] = seller
    sim.traders.append(seller)
    sim.current_tick = 0
    sim._run_auction("ABC", "open")
    assert sim.session_prints[-1]["volume"] == 10
    assert any(p["phase"] == "open" for p in sim.session_prints)


def test_midpoint_auction_matches_uncrossed_book():
    company = _co("ABC Inc", "Technology", "ABC")
    mm = MarketMaker("mm", 200000, 5000, 0)
    mm.symbol = "ABC"
    sim = Simulation(Exchange(), [mm], company=company, days=1, enable_session_prints=True)
    book = sim._book("ABC")
    buy = Order(mm.trader_id, Side.BUY, 99.0, 12, OrderType.LIMIT)
    buy.expiration_tick = 1000
    buy.reserved_cash = 99.0 * 12 * 1.001
    mm.money -= buy.reserved_cash
    sell = Order("other", Side.SELL, 101.0, 8, OrderType.LIMIT)
    sell.expiration_tick = 1000
    sell.reserved_shares = 8
    book.add_order_to_book(buy)
    book.add_order_to_book(sell)

    class _S:
        trader_id = "other"
        money = 0.0
        shares = 0
        name = "other"
        symbol = "ABC"

    seller = _S()
    sim.trader_map[seller.trader_id] = seller
    sim.traders.append(seller)
    sim.current_tick = 389
    sim._run_auction("ABC", "close")
    assert sim.session_prints[-1]["volume"] == 8
    assert abs(sim.session_prints[-1]["price"] - 100.0) < 1e-9


def test_sector_event_filtered_by_industry():
    a = _co("A", "Technology", "AAA")
    b = _co("B", "Finance", "BBB")
    traders = [MarketMaker("mma", 100000, 1000, 0), MarketMaker("mmb", 100000, 1000, 0)]
    traders[0].symbol = "AAA"
    traders[1].symbol = "BBB"
    sim = Simulation(
        Exchange(),
        traders,
        companies={"AAA": a, "BBB": b},
        days=1,
        enable_auctions=False,
    )
    event = generate_sector_event(0, "Technology")
    sim._fire_market_event(event)
    sa = sim.build_market_state("AAA", traders[0])
    sb = sim.build_market_state("BBB", traders[1])
    assert any(e.source == "sector" for e in sa.recent_events)
    assert all(e.source != "sector" for e in sb.recent_events)


def test_liquidity_event_sets_stress():
    company = _co("ABC Inc", "Technology", "ABC")
    mm = MarketMaker("mm", 100000, 1000, 0)
    sim = Simulation(Exchange(), [mm], company=company, days=1, enable_auctions=False)
    event = generate_liquidity_event(0)
    event.kind = "liquidity_dryup"
    event.magnitude = 0.05
    sim.current_tick = 10
    sim._fire_market_event(event)
    assert sim.liquidity_stress == stress_multiplier_from_event(event)
    assert sim.liquidity_stress_until > 10
    state = sim.build_market_state("ABC", mm)
    assert state.liquidity_stress > 1.0
    assert state.bid_depth is not None


def test_sector_apply_moves_matching_company():
    company = _co("ABC Inc", "Technology", "ABC")
    before = company.fundamental_value
    event = generate_sector_event(0, "Technology")
    apply_sector_event(company, event)
    assert company.fundamental_value != before or abs(event.magnitude) < 0.001


def test_new_trader_classes_construct():
    for cls in (MeanReversionTrader, BreakoutTrader, AttentionTrader):
        t = cls("x", 5000, 20, 0)
        assert t.trader_id is not None
