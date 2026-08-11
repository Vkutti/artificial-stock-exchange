from exchange.exchange import Exchange
from simulation.simulation import Simulation

from traders.random_trader import RandomTrader
from traders.market_maker import MarketMaker
from traders.fair_value_trader import FairValueTrader
from traders.momentum_trader import MomentumTrader
from traders.persistent_trader import PersistentTrader
from traders.sentiment_trader import SentimentTrader

from exchange.enums import Side

from company.company import Company

import random

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import mplfinance as mpf
from collections import defaultdict


exchange = Exchange()

traders = []

company = Company("ABC Incorporated", "Technology", 10000000, 2000000, 1000000, 3600000, 8000000, 1000000, 0.5)

names_1 = [
    "James", "Michael", "William", "David", "John",
    "Robert", "Joseph", "Thomas", "Charles", "Daniel",
    "Matthew", "Anthony", "Mark", "Donald", "Steven",
    "Paul", "Andrew", "Joshua", "Kenneth", "Kevin",
    "Brian", "George", "Edward", "Ronald", "Timothy",
    "Jason", "Jeffrey", "Ryan", "Jacob", "Nicholas", 
    "Aiden", "Asher", "Cameron", "Cooper", "Damian",
    "Evan", "Felix", "Finn", "Graham", "Harrison",
    "Hudson", "Jasper", "Kai", "Landon", "Liam",
    "Mason", "Nathaniel", "Oliver", "Parker", "Preston",
    "Reid", "Rowan", "Silas", "Theo", "Tristan",
    "Wesley", "Wyatt", "Zane", "Kieran", "Emmett", 
    "Austin", "Dylan", "Hunter", "Jordan", "Ethan",
    "Logan", "Noah", "Caleb", "Luke", "Connor",
    "Owen", "Eli", "Isaac", "Gabriel", "Julian",
    "Miles", "Dominic", "Vincent", "Victor", "Oscar",
    "Leon", "Joel", "Xavier", "Cole", "Blake",
    "Spencer", "Gavin", "Grant", "Trevor", "Max", 
    "James", "Michael", "William", "David", "John",
    "Robert", "Joseph", "Thomas", "Charles", "Daniel",
    "Matthew", "Anthony", "Mark", "Donald", "Steven",
    "Paul", "Andrew", "Joshua", "Kenneth", "Kevin",
    "Brian", "George", "Edward", "Ronald", "Timothy",
    "Jason", "Jeffrey", "Ryan", "Jacob", "Nicholas", 
    "Aiden", "Asher", "Cameron", "Cooper", "Damian",
    "Evan", "Felix", "Finn", "Graham", "Harrison",
    "Hudson", "Jasper", "Kai", "Landon", "Liam",
    "Mason", "Nathaniel", "Oliver", "Parker", "Preston",
    "Reid", "Rowan", "Silas", "Theo", "Tristan",
    "Wesley", "Wyatt", "Zane", "Kieran", "Emmett", 
    "Austin", "Dylan", "Hunter", "Jordan", "Ethan",
    "Logan", "Noah", "Caleb", "Luke", "Connor",
    "Owen", "Eli", "Isaac", "Gabriel", "Julian",
    "Miles", "Dominic", "Vincent", "Victor", "Oscar",
    "Leon", "Joel", "Xavier", "Cole", "Blake",
    "Spencer", "Gavin", "Grant", "Trevor", "Max", 
]

names_2 = [
    "Benjamin", "Samuel", "Alexander", "Patrick", "Jack",
    "Nathan", "Justin", "Aaron", "Adam", "Christian",
    "Tyler", "Zachary", "Eric", "Brandon", "Jonathan",
    "Scott", "Gregory", "Frank", "Raymond", "Jerry",
    "Dennis", "Walter", "Henry", "Douglas", "Peter",
    "Harold", "Carl", "Arthur", "Lawrence", "Sean", 
    "James", "Michael", "William", "David", "John",
    "Robert", "Joseph", "Thomas", "Charles", "Daniel",
    "Matthew", "Anthony", "Mark", "Donald", "Steven",
    "Paul", "Andrew", "Joshua", "Kenneth", "Kevin",
    "Brian", "George", "Edward", "Ronald", "Timothy",
    "Jason", "Jeffrey", "Ryan", "Jacob", "Nicholas", 
    "Aiden", "Asher", "Cameron", "Cooper", "Damian",
    "Evan", "Felix", "Finn", "Graham", "Harrison",
    "Hudson", "Jasper", "Kai", "Landon", "Liam",
    "Mason", "Nathaniel", "Oliver", "Parker", "Preston",
    "Reid", "Rowan", "Silas", "Theo", "Tristan",
    "Wesley", "Wyatt", "Zane", "Kieran", "Emmett", 
    "Austin", "Dylan", "Hunter", "Jordan", "Ethan",
    "Logan", "Noah", "Caleb", "Luke", "Connor",
    "Owen", "Eli", "Isaac", "Gabriel", "Julian",
    "Miles", "Dominic", "Vincent", "Victor", "Oscar",
    "Leon", "Joel", "Xavier", "Cole", "Blake",
    "Spencer", "Gavin", "Grant", "Trevor", "Max", 
]

names_3 = [
    "Austin", "Dylan", "Hunter", "Jordan", "Ethan",
    "Logan", "Noah", "Caleb", "Luke", "Connor",
    "Owen", "Eli", "Isaac", "Gabriel", "Julian",
    "Miles", "Dominic", "Vincent", "Victor", "Oscar",
    "Leon", "Joel", "Xavier", "Cole", "Blake",
    "Spencer", "Gavin", "Grant", "Trevor", "Max", 
    "James", "Michael", "William", "David", "John",
    "Robert", "Joseph", "Thomas", "Charles", "Daniel",
    "Matthew", "Anthony", "Mark", "Donald", "Steven",
    "Paul", "Andrew", "Joshua", "Kenneth", "Kevin",
    "Brian", "George", "Edward", "Ronald", "Timothy",
    "Jason", "Jeffrey", "Ryan", "Jacob", "Nicholas", 
    "Aiden", "Asher", "Cameron", "Cooper", "Damian",
    "Evan", "Felix", "Finn", "Graham", "Harrison",
    "Hudson", "Jasper", "Kai", "Landon", "Liam",
    "Mason", "Nathaniel", "Oliver", "Parker", "Preston",
    "Reid", "Rowan", "Silas", "Theo", "Tristan",
    "Wesley", "Wyatt", "Zane", "Kieran", "Emmett", 
    "Austin", "Dylan", "Hunter", "Jordan", "Ethan",
    "Logan", "Noah", "Caleb", "Luke", "Connor",
    "Owen", "Eli", "Isaac", "Gabriel", "Julian",
    "Miles", "Dominic", "Vincent", "Victor", "Oscar",
    "Leon", "Joel", "Xavier", "Cole", "Blake",
    "Spencer", "Gavin", "Grant", "Trevor", "Max", 
]

money = [1000, 2000, 5000, 8000, 10000, 20000, 50000]

for _ in range(10):
    traders.append(MarketMaker("MarketMaker", 250000, 50000, 100))

for _ in range(60):
    cash = random.choice(money)

    traders.append(RandomTrader(names_1[_], cash, 0, 0)) 

for _ in range(50):
    cash = random.choice(money)

    traders.append(FairValueTrader(names_2[_], cash, 0, 0))

for _ in range(40):
    cash = random.choice(money)

    traders.append(MomentumTrader(names_3[_], cash, 0, 0))

for _ in range(30):
    cash = random.choice(money)

    traders.append(PersistentTrader(names_1[_], cash, 0, 0))

for _ in range(30):
    cash = random.choice(money)

    traders.append(SentimentTrader(names_2[_], cash, 0, 0))


# simulation = Simulation(exchange, traders, 117000, company)
simulation = Simulation(exchange, traders, 468000, company)
# simulation = Simulation(exchange, traders, 1404000, company)
# simulation = Simulation(exchange, traders, 2808000, company)
# simulation = Simulation(exchange, traders, 5896800, company)

# Store each trader's starting portfolio value
initial_portfolio_values = {}

initial_price = company.fundamental_value

for trader in traders:
    initial_portfolio_values[trader.trader_id] = (
        trader.money +
        trader.shares * initial_price
    )

bid_data, ask_data, mid_data, fundamental_price, spread, volume, last_trade_price, fundamental_ticks, revenue, earnings, book_value, company_cash, debt = simulation.run()

# print(company)

trade_counts = {}

for trade in exchange.trade_history:
    trade_counts[trade.buy_trader_id] = trade_counts.get(trade.buy_trader_id, 0) + 1
    trade_counts[trade.sell_trader_id] = trade_counts.get(trade.sell_trader_id, 0) + 1

for trader in traders:
    print(
        trader.name,
        trade_counts.get(trader.trader_id, 0),
        type(trader).__name__, trader.name
    )

pairs = defaultdict(int)

final_price = exchange.get_last_trade_price()

if final_price is None:
    final_price = company.fundamental_value


# Cancel outstanding orders so that reserved
# cash/shares are returned to the trader.
for trader in traders:

    cancelled_orders = exchange.cancel_trader_orders(
        trader.trader_id
    )

    for order in cancelled_orders:

        if order.side == Side.BUY:
            trader.money += (
                order.price *
                order.remaining_quantity
            )

        else:
            trader.shares += order.remaining_quantity


pnl_stats = []

for trader in traders:
    initial_value = initial_portfolio_values[
        trader.trader_id
    ]

    final_value = (
        trader.money +
        trader.shares * final_price
    )

    pnl = final_value - initial_value

    if initial_value > 0:
        return_pct = (pnl / initial_value) * 100
    else:
        return_pct = 0

    pnl_stats.append({
        "name": trader.name,
        "type": type(trader).__name__,
        "initial_value": initial_value,
        "final_value": final_value,
        "pnl": pnl,
        "return_pct": return_pct,
        "cash": trader.money,
        "shares": trader.shares,
        "trades": trade_counts.get(
            trader.trader_id,
            0
        )
    })

for trade in exchange.trade_history:
    buyer = type(simulation.trader_map[trade.buy_trader_id]).__name__
    seller = type(simulation.trader_map[trade.sell_trader_id]).__name__

    key = tuple(sorted((buyer, seller)))
    pairs[key] += 1

for pair, count in sorted(pairs.items(), key=lambda x: x[1], reverse=True):
    print(pair, count)

trade_ticks = [trade.tick for trade in exchange.trade_history]
trade_prices = [trade.price for trade in exchange.trade_history]

print("Trades:", len(exchange.trade_history))
print("Last price:", exchange.get_last_trade_price())

print("\n========== TRADER P&L ==========")

for stats in sorted(
    pnl_stats,
    key=lambda x: x["pnl"],
    reverse=True
):

    print(
        f"{stats['name']:15} "
        f"{stats['type']:20} "
        f"P&L: ${stats['pnl']:>10,.2f} "
        f"Return: {stats['return_pct']:>7.2f}% "
        f"Trades: {stats['trades']}"
    )

# ==========================================
# P&L BY TRADER TYPE
# ==========================================

type_stats = defaultdict(list)

for stats in pnl_stats:
    type_stats[stats["type"]].append(stats)


print("\n========== P&L BY STRATEGY ==========")

for trader_type, stats_list in sorted(
    type_stats.items()
):

    total_pnl = sum(
        stats["pnl"]
        for stats in stats_list
    )

    average_pnl = (
        total_pnl /
        len(stats_list)
    )

    average_return = (
        sum(
            stats["return_pct"]
            for stats in stats_list
        )
        / len(stats_list)
    )

    total_trades = sum(
        stats["trades"]
        for stats in stats_list
    )

    print(
        f"{trader_type:20} "
        f"Traders: {len(stats_list):3} "
        f"Avg P&L: ${average_pnl:>10,.2f} "
        f"Avg Return: {average_return:>7.2f}% "
        f"Trades: {total_trades:,}"
    )

event_ticks = range(len(fundamental_price))

# STEP = max(1, len(trade_ticks) // 11.7)

plt.figure(figsize=(15, 7))

plt.plot(
    trade_ticks,
    trade_prices,
    color="tab:blue",
    linewidth=0.8,
    label="Trade Price",
)

plt.plot(
    fundamental_ticks,
    fundamental_price,
    color="tab:red",
    linewidth=2,
    linestyle="--",
    label="Fundamental Value",
)

plt.title("Market Price vs Fundamental Value")
plt.xlabel("Simulation Tick")
plt.ylabel("Price")

plt.grid(alpha=0.3)
plt.legend()

plt.tight_layout()
plt.show()