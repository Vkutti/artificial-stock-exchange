# Artificial Stock Exchange with Trading Agents

Python limit-order-book market with heterogeneous agents, multi-name listings, and a NYSE-style trading-minute clock.

## Run

```bash
python main.py --days 5 --seed 42
python main.py --days 21 --seed 7
pytest
python experiments/stylized_facts.py --seeds 30 --days 21
```

`--seed` makes runs reproducible. Without a fixed seed, strategy P&L is a single noisy sample.

## Time & session

- 1 tick = 1 trading minute; 09:30–16:00 → 390 minutes/day
- Open/close **session prints** (mid/BBO markers — not a full cross auction)
- Per-symbol circuit breakers (~±7% vs a **rolling** EMA reference, with halt + cooldown)

## Market mechanics

- Price-time CLOB, LIMIT + MARKET (buys capped by reserved `ask×1.05`)
- `$0.01` tick grid; bps spreads on market makers
- Fees, collateral reserve/refund, self-trade prevention
- Order/trade timestamps use **simulation ticks**, not wall clock

## Information model

Agents see a public view: BBO, tape copy, sentiment snapshot, symbol-filtered headlines (sign/intensity), and a **private FV estimate** = true FV × (1 + fixed bias + mean-reverting noise). They do not get the live `Company` object.

## Return drivers

| Driver | Implementation |
|--------|----------------|
| Order flow | CLOB matching across agent types |
| Fundamentals | Dailyized PE×EPS path per company |
| Macro / rates | Shared `Economy.risk_free_rate` → interest + PE |
| Flow regimes | `Economy.flow_multiplier` scales participation |
| News / social | Sign-balanced firm events (tagged by symbol) |

## Listings

Default names: **ABC** (Technology), **NBK** (Finance), **HLX** (Healthcare).

## Research checks

Sanity flags in `main.py` (horizon-aware spread gate: 5–120 bps for `days<=5`, else 5–80).

Multi-seed stylized facts (`experiments/stylized_facts.py`):

- Excess kurtosis of daily returns
- Return AC(1) and squared-return AC(1) (vol clustering)
- Strategy average returns with 95% CI across seeds

## Design decisions and limitations

- **Session prints ≠ auctions.** Open/close marks a price on the tape; they do not uncross resting interest or create print volume from a clearing algorithm.
- **FV is an estimate, not a secret oracle dump**, but estimates stay anchored near true FV, so price still tracks fundamentals closely.
- **Long-only.** No short selling yet.
- **Breaker** uses a rolling EMA of trade prices plus cooldown after a halt, not a static prior-close band all day.
- **Book** uses `dict` price levels with `min`/`max` best-price scans — fine at current scale; heap/sorted levels are a later optimization if profiling requires it.
- Dividends hit company books only; holders are not paid yet.

## Layout

```
exchange/      OrderBook, ticks, MarketState / PublicHeadline
company/       Company, Economy, sector, events
traders/       strategies
simulation/    SimClock, Simulation, Event
experiments/   multi-seed stylized facts
main.py        CLI entry (`--days`, `--seed`)
tests/
```

## Roadmap

**Done:** realism core, multi-name, session prints, rolling breakers, observation contract, seed/CLI, stylized-fact harness.

**Next (UI platform):** run recorder, FastAPI replay, exchange front-end (chart/book/tape/scrubber), optional user paper trading.

**Later:** shorts, ex-div to holders, earnings calendar, real auction cross, maker–taker, options.
