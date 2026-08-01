from exchange.exchange import Exchange
from simulation.simulation import Simulation

from traders.random_trader import RandomTrader
from traders.market_maker import MarketMaker
import random

import matplotlib.pyplot as plt
import numpy as np

exchange = Exchange()

traders = []
names = ["Bob", "James", "Jim", "Jimmy", "Bobby", "Tim", "Timmy", "Jeff", "Venkat"]
money = [10000, 20000, 50000, 80000, 100000, 150000]

traders.append(MarketMaker("MarketMaker", 250000, 2500, 100))

for _ in range(25):
    cash = random.choice(money)

    traders.append(RandomTrader(names[random.randrange(len(names))], cash, cash // 100, 0)) 

simulation = Simulation(exchange, traders, 117000)

bid_data, ask_data, mid_data = simulation.run()

# print(bid_data)
# print(ask_data)

# plt.plot(bid_data, label="Bid Price")
# plt.plot(ask_data, label="Ask Price")

plt.plot(mid_data, label="Mid Price")

plt.legend()
plt.show()

print("Trades:", len(exchange.trade_history))
print("Last price:", exchange.get_last_trade_price())