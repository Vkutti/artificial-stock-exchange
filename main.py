from exchange.exchange import Exchange
from simulation.simulation import Simulation

from traders.random_trader import RandomTrader
from traders.market_maker import MarketMaker
from traders.fair_value_trader import FairValueTrader
from traders.momentum_trader import MomentumTrader
from traders.persistent_trader import PersistentTrader

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
    "Wesley", "Wyatt", "Zane", "Kieran", "Emmett"
]

names_2 = [
    "Benjamin", "Samuel", "Alexander", "Patrick", "Jack",
    "Nathan", "Justin", "Aaron", "Adam", "Christian",
    "Tyler", "Zachary", "Eric", "Brandon", "Jonathan",
    "Scott", "Gregory", "Frank", "Raymond", "Jerry",
    "Dennis", "Walter", "Henry", "Douglas", "Peter",
    "Harold", "Carl", "Arthur", "Lawrence", "Sean"
]

names_3 = [
    "Austin", "Dylan", "Hunter", "Jordan", "Ethan",
    "Logan", "Noah", "Caleb", "Luke", "Connor",
    "Owen", "Eli", "Isaac", "Gabriel", "Julian",
    "Miles", "Dominic", "Vincent", "Victor", "Oscar",
    "Leon", "Joel", "Xavier", "Cole", "Blake",
    "Spencer", "Gavin", "Grant", "Trevor", "Max"
]

money = [1000, 2000, 5000, 8000, 10000, 20000, 50000]

for _ in range(5):
    traders.append(MarketMaker("MarketMaker", 250000, 50000, 100))

for _ in range(60):
    cash = random.choice(money)

    traders.append(RandomTrader(names_1[_], cash, 0, 0)) 

for _ in range(20):
    cash = random.choice(money)

    traders.append(FairValueTrader(names_2[_], cash, 0, 0))

for _ in range(15):
    cash = random.choice(money)

    traders.append(MomentumTrader(names_3[_], cash, 0, 0))

for _ in range(10):
    cash = random.choice(money)

    traders.append(PersistentTrader(names_1[_], cash, 0, 0))


# simulation = Simulation(exchange, traders, 117000, company)
simulation = Simulation(exchange, traders, 468000, company)
# simulation = Simulation(exchange, traders, 5896800, company)

bid_data, ask_data, mid_data, fundamental_price, spread, volume, last_trade_price, fundamental_ticks, revenue, earnings, book_value, company_cash, debt = simulation.run()

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

event_ticks = range(len(fundamental_price))

STEP = max(1, len(trade_ticks) // 11.7)

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