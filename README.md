# Artificial Stock Exchange with Trading Agents

A Python-based limit order book simulator that models a financial market populated by multiple autonomous trading agents.

The goal of this project is to build a realistic market simulation that can be used to study market microstructure, agent interactions, price discovery, liquidity, and algorithmic trading strategies across trading days.

---

## Overview

Independent agents submit limit and market orders into a central limit order book. Price emerges from order flow—there is no scripted path. A listed `Company` supplies a PE-based fundamental; news, social, and economic events move sentiment (and, for news/macro, fundamentals) on a calibrated multi-day cadence.

### Time model

- **1 simulation tick = 1 trading minute**
- **NYSE-style session:** 09:30–16:00 → **390 trading minutes per day**
- Configure length with **`days=`** (e.g. `Simulation(..., days=5)`)
- Plots use a **trading-days** axis
- Optional `playback_delay_sec` for live demo pacing

### Multi-symbol scaffold

The exchange hosts **per-symbol order books** (no cross-matching). `main.py` currently lists one name (`ABC`); adding more listings is the next step toward an NYSE-style multi-company market.

---

## Features

- Price-time priority CLOB (multi-symbol ready)
- Market orders (sweep; remainder cancelled) and limit orders
- TTL, cancel, self-trade prevention with exact collateral refunds
- Transaction fees on fills
- Company fundamentals with **dailyized** growth and mild PE/growth mean-reversion
- Calibrated news / social / economic events (stable over weeks, not death spirals)
- Heterogeneous agents: MM, noise, fair value, momentum, persistent, sentiment, news, index fund
- Diagnostics: FV path, events/day, fees, cash/share conservation

---

## Running

```bash
python main.py
pytest
```

In [`main.py`](main.py):

```python
DAYS = 5      # also try 1, 21, 63
```

Dependencies: see [`requirements.txt`](requirements.txt) (`numpy`, `matplotlib`, `pandas`, `mplfinance`, `pytest`).

---

## Trader types

| Trader | Role |
|--------|------|
| Market Maker | Inventory-aware two-sided quotes (minute refresh) |
| Random | Uninformed flow |
| Fair Value | Trades gaps vs fundamental |
| Momentum | Short-term trend following |
| Persistent | Steady accumulation (lifts the offer) |
| Sentiment | Smoothed sentiment + recent headlines |
| News | One reaction per news/macro event |
| Index Fund | Slow passive buy flow |

---

## Company & events

Each listing is a `Company` with a `symbol`, sector multipliers, and financials. Company updates run **once per trading day** with dailyized growth (not annual shocks every day).

| Source | Cadence (approx.) | Effect |
|--------|-------------------|--------|
| Sentiment | every ~15 minutes | Regime random walk |
| News | ~1 per day | Mild fundamental + sentiment (±3% FV cap) |
| Social | ~2 per day | Sentiment only |
| Economic | ~weekly | Mild PE / growth |
| Company update | once per day | Dailyized earnings path + mean-reversion |

Event templates are **sign-balanced** so multi-week runs behave like a mild random walk around fundamental rather than a forced crash.

---

## Architecture (high level)

```
traders/          agent strategies (decide_action → Action)
exchange/         Exchange + per-symbol OrderBook, Order, Trade, MarketState
company/          Company, Sector, Sentiment, news/social/economic events
simulation/       SimClock, Simulation (event heap, days=, fees, metrics)
main.py           population, DAYS, P&L, day-axis plot
tests/            exchange, clock, symbols, accounting, events, traders
```

---

## Current status / roadmap

**Done:** calendar-minute engine, multi-day stability, fees + collateral correctness, news/index traders, multi-symbol books scaffold.

**Next:** multiple simultaneous listings, correlated sector shocks, richer microstructure (auctions/halts), deeper day-level analytics.

---

## Purpose

Learning and research platform for quantitative finance, market microstructure, algorithmic trading, agent-based modeling, and exchange design.
