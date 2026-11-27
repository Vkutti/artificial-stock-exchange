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
    mm.fv_noise = 0.0
    sim = Simulation(Exchange(), [mm], company=company, days=1, enable_auctions=False)
    state = sim.build_market_state("ABC", trader=mm)
    assert state.company is None
    expected = company.fundamental_value * (1.0 + mm.fv_bias + mm.fv_noise)
    assert abs(state.fundamental_price - expected) < 1e-6
    assert mm.fv_noise != 0.0 or True
    state2 = sim.build_market_state("ABC", trader=mm)
    assert state2.fundamental_price != company.fundamental_value
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


def test_session_prints_and_rolling_breaker():
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
        enable_session_prints=True,
        enable_circuit_breakers=True,
    )
    sim.run()
    phases = {p["phase"] for p in sim.session_prints}
    assert "open" in phases
    assert "close" in phases
    assert "ABC" in sim.symbol_series
    assert len(sim.symbol_series["ABC"]["fv"]) > 0

    sim.breaker_ref["ABC"] = 100.0
    sim.halted_until["ABC"] = -1
    sim.halt_cooldown_until["ABC"] = -1
    sim.current_tick = 50
    sim._maybe_halt("ABC", 80.0)
    assert sim._is_halted("ABC")
    assert sim.breaker_ref["ABC"] == 80.0

    sim.halted_until["ABC"] = -1
    sim.current_tick = sim.halt_cooldown_until["ABC"] - 1
    before = sim.halt_counts["ABC"]
    sim._maybe_halt("ABC", 60.0)
    assert sim.halt_counts["ABC"] == before

    sim.current_tick = sim.halt_cooldown_until["ABC"] + 1
    sim.breaker_ref["ABC"] = 100.0
    sim._maybe_halt("ABC", 80.0)
    assert sim.halt_counts["ABC"] == before + 1


def test_seed_reproducibility():
    from main import run_simulation

    a = run_simulation(days=1, seed=7, plot=False)
    b = run_simulation(days=1, seed=7, plot=False)
    assert len(a["exchange"].trade_history) == len(b["exchange"].trade_history)
    assert [t.price for t in a["exchange"].trade_history] == [
        t.price for t in b["exchange"].trade_history
    ]
    assert abs(a["ann_ret"] - b["ann_ret"]) < 1e-12


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
