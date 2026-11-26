from exchange.exchange import Exchange
from exchange.order import Order
from exchange.enums import Side, OrderType
from exchange.ticks import round_to_tick
from simulation.simulation import Simulation
from traders.market_maker import MarketMaker
from traders.random_trader import RandomTrader
from traders.action import Action
from company.company import Company


def test_buy_cancel_restores_exact_cash_with_fees():
    company = Company("T", "Technology", 1e6, 1e5, 1e5, 5e5, 1e6, 1e5, 0.2, symbol="T")
    mm = MarketMaker("Elena-MM0", 10_000, 100, 0)
    exchange = Exchange()
    sim = Simulation(exchange, [mm], company=company, days=1, fee_rate=0.001)

    starting_cash = mm.money
    order = Order(mm.trader_id, Side.BUY, 50, 10, OrderType.LIMIT)
    order.expiration_tick = 100
    reserved = order.price * order.quantity * (1.0 + sim.fee_rate)
    mm.money -= reserved
    order.reserved_cash = reserved

    exchange.submit_order(order, 0)
    cancelled = exchange.cancel_trader_orders(mm.trader_id)
    assert order in cancelled

    for cancelled_order in cancelled:
        sim._refund_order(cancelled_order)

    assert abs(mm.money - starting_cash) < 1e-9


def test_unique_trader_names_helper_pattern():
    names = [f"Alex-RND{i}" for i in range(5)] + [f"Sam-MM{i}" for i in range(3)]
    assert len(names) == len(set(names))


def test_short_sim_cash_and_share_conservation():
    company = Company("ABC", "Technology", 1e7, 2e6, 1e6, 3.6e6, 8e6, 1e6, 0.5, symbol="ABC")
    traders = [
        MarketMaker("A-MM0", 250000, 5000, 0),
        MarketMaker("B-MM1", 250000, 5000, 0),
    ]
    for i in range(20):
        traders.append(RandomTrader(f"R-RND{i}", 8000, 20, 0))

    exchange = Exchange()
    sim = Simulation(exchange, traders, company=company, days=1, fee_rate=0.001)

    initial_cash = sum(t.money for t in traders)
    initial_shares = sum(t.shares for t in traders)

    sim.run()

    final_cash = sum(t.money for t in traders)
    final_shares = sum(t.shares for t in traders)

    assert abs(final_cash - (initial_cash - sim.total_fees)) < 1e-4
    assert final_shares == initial_shares
    assert all(t.money >= -1e-6 for t in traders)


def test_market_buy_cannot_walk_past_collateral_cap():
    company = Company("T", "Technology", 1e6, 1e5, 1e5, 5e5, 1e6, 1e5, 0.2, symbol="T")
    buyer = MarketMaker("buyer", 600, 0, 0)
    seller = MarketMaker("seller", 0, 100, 0)
    exchange = Exchange()
    sim = Simulation(
        exchange,
        [buyer, seller],
        company=company,
        days=1,
        fee_rate=0.001,
        enable_auctions=False,
        enable_circuit_breakers=False,
    )

    exchange.submit_order(
        Order(seller.trader_id, Side.SELL, 100, 1, OrderType.LIMIT), 0
    )
    high = Order(seller.trader_id, Side.SELL, 200, 10, OrderType.LIMIT)
    high.expiration_tick = 1000
    seller.shares -= 10
    high.reserved_shares = 10
    exchange.submit_order(high, 0)

    sim.submit_action(buyer, Action(Side.BUY, 100, 5, OrderType.MARKET), 1)

    assert buyer.money >= -1e-6
    assert buyer.shares <= 1


def test_limit_reserve_uses_snapped_price():
    company = Company("T", "Technology", 1e6, 1e5, 1e5, 5e5, 1e6, 1e5, 0.2, symbol="T")
    trader = MarketMaker("t", 10_000, 0, 0)
    exchange = Exchange(tick_size=0.01)
    sim = Simulation(
        exchange,
        [trader],
        company=company,
        days=1,
        fee_rate=0.001,
        enable_auctions=False,
        enable_circuit_breakers=False,
    )
    start = trader.money
    raw = 10.126
    snapped = round_to_tick(raw, 0.01)
    sim.submit_action(trader, Action(Side.BUY, raw, 10, OrderType.LIMIT), 0)
    expected_reserved = snapped * 10 * 1.001
    assert abs((start - trader.money) - expected_reserved) < 1e-6


def test_reset_refunds_collateral():
    company = Company("T", "Technology", 1e6, 1e5, 1e5, 5e5, 1e6, 1e5, 0.2, symbol="T")
    trader = MarketMaker("t", 10_000, 50, 0)
    exchange = Exchange()
    sim = Simulation(
        exchange,
        [trader],
        company=company,
        days=1,
        fee_rate=0.001,
        enable_auctions=False,
        enable_circuit_breakers=False,
    )
    start_cash = trader.money
    start_shares = trader.shares
    sim.submit_action(trader, Action(Side.BUY, 20, 5, OrderType.LIMIT), 0)
    sim.submit_action(trader, Action(Side.SELL, 30, 5, OrderType.LIMIT), 0)
    assert trader.money < start_cash or trader.shares < start_shares
    sim.reset()
    assert abs(trader.money - start_cash) < 1e-6
    assert trader.shares == start_shares
