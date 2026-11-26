from exchange.exchange import Exchange
from exchange.order import Order
from exchange.enums import Side, OrderType
from simulation.simulation import Simulation
from traders.market_maker import MarketMaker
from traders.random_trader import RandomTrader
from company.company import Company
from company.economy import Economy
from company.economic_event import apply_economic_event, generate_economic_event


def _co(name, industry, symbol):
    return Company(name, industry, 1e7, 2e6, 1e6, 3.6e6, 8e6, 1e6, 0.5, symbol=symbol)


def test_observation_hides_true_company_and_uses_estimate():
    company = _co("ABC Inc", "Technology", "ABC")
    mm = MarketMaker("mm", 100000, 1000, 0)
    mm.fv_bias = 0.05
    sim = Simulation(Exchange(), [mm], company=company, days=1, enable_auctions=False)
    state = sim.build_market_state("ABC", trader=mm)
    assert state.company is None
    assert abs(state.fundamental_price - company.fundamental_value * 1.05) < 1e-6
    assert all(not hasattr(e, "magnitude") or isinstance(e.magnitude, float) for e in state.recent_events)


def test_symbol_filtered_events():
    a = _co("A", "Technology", "AAA")
    b = _co("B", "Finance", "BBB")
    traders = [
        MarketMaker("mma", 100000, 1000, 0),
        MarketMaker("mmb", 100000, 1000, 0),
    ]
    traders[0].symbol = "AAA"
    traders[1].symbol = "BBB"
    sim = Simulation(
        Exchange(),
        traders,
        companies={"AAA": a, "BBB": b},
        days=1,
        enable_auctions=False,
    )
    from company.news_event import generate_news_event

    ea = generate_news_event(0, a.name, symbol="AAA")
    eb = generate_news_event(0, b.name, symbol="BBB")
    sim._fire_market_event(ea, a)
    sim._fire_market_event(eb, b)
    sa = sim.build_market_state("AAA", traders[0])
    sb = sim.build_market_state("BBB", traders[1])
    assert all(e.symbol in (None, "AAA") or e.source == "economic" for e in sa.recent_events)
    assert all(e.symbol != "BBB" for e in sa.recent_events if e.source == "news")
    assert all(e.symbol != "AAA" for e in sb.recent_events if e.source == "news")


def test_economy_moves_pe():
    company = _co("ABC Inc", "Technology", "ABC")
    economy = Economy(0.05)
    before = company.pe_ratio
    economy.risk_free_rate = 0.08
    company.apply_economy(economy)
    assert company.pe_ratio < before


def test_auctions_and_halts_in_short_run():
    company = _co("ABC Inc", "Technology", "ABC")
    traders = [MarketMaker(f"mm{i}", 200000, 5000, 0) for i in range(3)]
    for i in range(10):
        traders.append(RandomTrader(f"r{i}", 10000, 30, 0))
    sim = Simulation(
        Exchange(),
        traders,
        company=company,
        days=2,
        fee_rate=0.001,
        enable_auctions=True,
        enable_circuit_breakers=True,
    )
    sim.run()
    phases = {p["phase"] for p in sim.auction_prints}
    assert "open" in phases
    assert "close" in phases

    sim.prior_close["ABC"] = 100.0
    sim.current_tick = 50
    sim._maybe_halt("ABC", 80.0)
    assert sim._is_halted("ABC")


def test_multi_symbol_conservation():
    companies = {
        "AAA": _co("A", "Technology", "AAA"),
        "BBB": _co("B", "Finance", "BBB"),
    }
    traders = []
    for i, sym in enumerate(["AAA", "BBB"]):
        mm = MarketMaker(f"mm{i}", 200000, 4000, 0)
        mm.symbol = sym
        traders.append(mm)
        for j in range(8):
            r = RandomTrader(f"r{sym}{j}", 8000, 20, 0)
            r.symbol = sym
            traders.append(r)

    sim = Simulation(
        Exchange(),
        traders,
        companies=companies,
        days=1,
        fee_rate=0.001,
    )
    initial_cash = sum(t.money for t in traders)
    initial_shares = sum(t.shares for t in traders)
    sim.run()
    assert abs(sum(t.money for t in traders) - (initial_cash - sim.total_fees)) < 1e-3
    assert sum(t.shares for t in traders) == initial_shares
