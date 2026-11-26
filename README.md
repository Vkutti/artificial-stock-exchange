# Artificial Stock Exchange with Trading Agents

Python limit-order-book market with heterogeneous agents, multi-name listings, and a NYSE-style trading-minute clock.

## Time & session

- 1 tick = 1 trading minute; 09:30–16:00 → 390 minutes/day
- Configure with `DAYS` in `main.py` (`5`, `21`, `63`, `252`)
- Open/close auction prints; continuous trading between
- Per-symbol circuit breakers (~±7% vs prior close)

## Market mechanics

- Price-time CLOB, LIMIT + MARKET (market buys capped by reserved `ask×1.05`)
- `$0.01` tick grid; bps spreads on market makers
- Fees, collateral reserve/refund, self-trade prevention
- No negative cash on fills; `reset()` refunds resting collateral

## Information model

Agents see a **public** view only: BBO, tape copy, sentiment snapshot, symbol-filtered headlines (sign/intensity, not raw shock size), noisy private FV estimate (`fv_bias`). They do **not** receive the live `Company` object or true fundamental.

## Return drivers

| Driver | Implementation |
|--------|----------------|
| Order flow | CLOB matching across agent types |
| Fundamentals | Dailyized PE×EPS path per company |
| Macro / rates | Shared `Economy.risk_free_rate` → interest + PE |
| Flow regimes | `Economy.flow_multiplier` scales participation |
| News / social | Sign-balanced firm events (tagged by symbol) |
| Sector | Init multipliers; macro hits all names |

## Listings

`main.py` runs three names by default: **ABC** (Technology), **NBK** (Finance), **HLX** (Healthcare), each with dedicated MMs and flow traders.

## Run

```bash
python main.py
pytest
```

Year gate: set `DAYS = 252`, then check printed sanity flags (FV return, vol, spread bps, conservation, auctions, no negative cash).

## Layout

```
exchange/     OrderBook, ticks, MarketState / PublicHeadline
company/      Company, Economy, sector, news/social/economic events
traders/      MM, noise, FV, momentum, persistent, sentiment, news, index
simulation/   SimClock, Simulation (events, auctions, halts)
tests/        accounting, exchange, events, traders, phase2
```

## Roadmap status

**Done:** Phase 1 realism (ticks/bps/events) + Phase 2 (integrity, observation contract, economy/flow, multi-name, auctions, breakers).

**Later:** short selling, ex-div to holders, earnings calendar vs consensus, options, maker–taker fees.
