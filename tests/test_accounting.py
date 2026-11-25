from exchange.exchange import Exchange
from exchange.order import Order
from exchange.enums import Side, OrderType
from simulation.simulation import Simulation
from traders.market_maker import MarketMaker
from traders.random_trader import RandomTrader
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

    for trader in traders:
        for order in exchange.cancel_trader_orders(trader.trader_id):
            sim._refund_order(order)

    final_cash = sum(t.money for t in traders)
    final_shares = sum(t.shares for t in traders)

    assert abs(final_cash - (initial_cash - sim.total_fees)) < 1e-4
    assert final_shares == initial_shares
