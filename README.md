# Artificial Stock Exchange with Trading Agents

A Python-based limit order book simulator that models a financial market populated by multiple autonomous trading agents.

The goal of this project is to build a realistic market simulation that can be used to study market microstructure, agent interactions, price discovery, liquidity, and algorithmic trading strategies.

This is an active project and new trader types, market mechanics, and analytics are continuously being added.

---

## Overview

The simulator implements a central limit order book where independent trading agents continuously submit limit and market orders.

Each trader follows its own decision-making process while interacting with every other participant through the exchange.

The market evolves entirely from these interactions—there is no scripted price movement.

Current simulation includes:

- Central Limit Order Book (CLOB)
- Order matching engine
- Market orders
- Limit orders
- Order expiration (TTL)
- Trade history
- Bid / Ask tracking
- Mid-price tracking
- Volume tracking
- Fundamental value simulation

---

## Current Status

This project is actively under development.

Recent work includes:
- Agent scheduling using stochastic waiting times
- Inventory-aware market makers
- Fundamental value process
- Momentum and fair value traders

Upcoming work focuses on improving market realism with additional trader behaviors, transaction costs, and richer market microstructure.

---

## Trader Types

### Market Maker

Provides continuous liquidity by quoting both bid and ask prices.

Features:

- Inventory-aware quoting
- Dynamic bid/ask adjustment
- Inventory skew
- Fixed spread management
- Quote refresh intervals

---

### Random (Noise) Trader

Represents uninformed market participants.

Features:

- Random buy/sell decisions
- Market and limit orders
- Randomized order prices
- Random order sizes
- Individual trading frequency

---

### Fair Value Trader

Attempts to trade whenever the market price deviates from the simulated fundamental value.

Features:

- Individual valuation thresholds
- Fundamental price comparison
- Mean-reversion behavior

---

### Momentum Trader

Attempts to exploit short-term price trends.

Features:

- Recent price analysis
- Momentum detection
- Trend following
- Market order execution

---

## Exchange Features

- Price-time priority matching
- Partial fills
- Order cancellation
- Order expiration
- Trade recording
- Best bid / ask updates
- Spread calculation
- Volume tracking

---

## Market Simulation

Each trader acts independently according to an exponentially distributed waiting time.

At every simulation step:

1. Traders whose waiting time has elapsed become active.
2. Active traders observe the current market.
3. Traders decide whether to submit one or more orders.
4. Orders are matched through the exchange.
5. Expired orders are removed.
6. Market statistics are recorded.

---

## Visualization

The simulator records several market metrics during execution.

Examples include:

- Mid Price
- Bid Price
- Ask Price
- Spread
- Fundamental Price
- Trading Volume

These metrics can be plotted using Matplotlib.

---

## Technologies

- Python
- Matplotlib
- NumPy

---

## Purpose

This project is intended as a learning and research platform for:

- Quantitative Finance
- Market Microstructure
- Algorithmic Trading
- Agent-Based Modeling
- Simulation Systems
- Exchange Design

The long-term goal is to create a realistic experimental environment for developing and testing trading strategies.
