from exchange.exchange import Exchange
from simulation.simulation import Simulation
from simulation.clock import MINUTES_PER_DAY, SimClock

from traders.random_trader import RandomTrader
from traders.market_maker import MarketMaker
from traders.fair_value_trader import FairValueTrader
from traders.momentum_trader import MomentumTrader
from traders.persistent_trader import PersistentTrader
from traders.sentiment_trader import SentimentTrader
from traders.news_trader import NewsTrader
from traders.index_fund_trader import IndexFundTrader

from exchange.enums import Side

from company.company import Company

import random

import matplotlib.pyplot as plt
from collections import defaultdict

# Trading-day presets (1 tick = 1 trading minute, 390 min/day)
# DAYS = 1
DAYS = 5
# DAYS = 21   # ~1 trading month
# DAYS = 63   # ~1 quarter

exchange = Exchange()
traders = []

company = Company(
    "ABC Incorporated",
    "Technology",
    10000000,
    2000000,
    1000000,
    3600000,
    8000000,
    1000000,
    0.5,
    symbol="ABC",
)

FIRST_NAMES = [
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
    "Benjamin", "Samuel", "Alexander", "Patrick", "Jack",
    "Nathan", "Justin", "Aaron", "Adam", "Christian",
    "Tyler", "Zachary", "Eric", "Brandon", "Jonathan",
    "Scott", "Gregory", "Frank", "Raymond", "Jerry",
    "Dennis", "Walter", "Henry", "Douglas", "Peter",
    "Harold", "Carl", "Arthur", "Lawrence", "Sean",
    "Elena", "Priya", "Marcus", "Sofia", "Nina",
    "Omar", "Iris", "Leo", "Ava", "Nora",
    "Hugo", "Clara", "Ivy", "Jude", "Vera",
    "Quinn", "Remy", "Sage", "Tess", "Wade",
    "Yuki", "Zoe", "Amir", "Bea", "Cody",
    "Drew", "Elle", "Faye", "Gus", "Hope",
    "Ian", "Jade", "Kyle", "Lana", "Moe",
    "Nell", "Orion", "Pax", "Rita", "Skye",
    "Troy", "Uma", "Vince", "Willa", "Xander",
    "Yael", "Zara", "Brooks", "Casey", "Devon",
    "Eden", "Finley", "Gray", "Harper", "Indigo",
    "Jules", "Kendall", "Lane", "Morgan", "Noel",
    "Oakley", "Peyton", "Reese", "Shannon", "Taylor",
    "Val", "Winter", "Ash", "Blair", "CameronX",
    "Dallas", "Emerson", "Frankie", "Hayden", "Jamie",
    "Kelly", "LoganX", "Marley", "ParkerX", "QuinnX",
    "Riley", "Sawyer", "Toby", "Alex", "Chris",
    "Sam", "Pat", "Robin", "JordanX", "Terry",
    "Kim", "Lee", "Tracy", "Dana", "Leslie",
    "ShannonX", "Carey", "Adrian", "Sidney", "Bernie",
    "Jackie", "Ronnie", "Stevie", "Bill", "Ted",
    "Ned", "Fred", "Al", "Cal", "Sal",
]

name_pool = list(dict.fromkeys(FIRST_NAMES))
random.shuffle(name_pool)
_name_index = 0


def next_name(strategy_tag, index):
    global _name_index
    if _name_index >= len(name_pool):
        first = f"Trader{_name_index}"
    else:
        first = name_pool[_name_index]
    _name_index += 1
    return f"{first}-{strategy_tag}{index}"


def starter_inventory(cash):
    shares = random.randint(0, max(1, int(cash // 40)))
    return shares


money = [1000, 2000, 5000, 8000, 10000, 20000, 50000, 100000]

for i in range(10):
    traders.append(MarketMaker(next_name("MM", i), 250000, 15000, 0))

for i in range(60):
    cash = random.choice(money)
    traders.append(RandomTrader(next_name("RND", i), cash, starter_inventory(cash), 0))

for i in range(50):
    cash = random.choice(money)
    traders.append(FairValueTrader(next_name("FV", i), cash, starter_inventory(cash), 0))

for i in range(40):
    cash = random.choice(money)
    traders.append(MomentumTrader(next_name("MOM", i), cash, starter_inventory(cash), 0))

for i in range(30):
    cash = random.choice(money)
    traders.append(PersistentTrader(next_name("PER", i), cash, starter_inventory(cash), 0))

for i in range(30):
    cash = random.choice(money)
    traders.append(SentimentTrader(next_name("SENT", i), cash, starter_inventory(cash), 0))

for i in range(20):
    cash = random.choice(money)
    traders.append(NewsTrader(next_name("NEWS", i), cash, starter_inventory(cash), 0))

for i in range(10):
    cash = random.choice(money)
    traders.append(IndexFundTrader(next_name("IDX", i), cash * 2, starter_inventory(cash), 0))

assert len({t.name for t in traders}) == len(traders), "Trader names must be unique"

simulation = Simulation(
    exchange,
    traders,
    company=company,
    days=DAYS,
    verbose=False,
    fee_rate=0.001,
    playback_delay_sec=0.0,
)

initial_portfolio_values = {}
initial_price = company.fundamental_value
initial_fv = company.fundamental_value
initial_total_cash = sum(t.money for t in traders)
initial_total_shares = sum(t.shares for t in traders)

for trader in traders:
    initial_portfolio_values[trader.trader_id] = trader.money + trader.shares * initial_price

initial_total_mtm = sum(initial_portfolio_values.values())

bid_data, ask_data, mid_data, fundamental_price, spread, volume, last_trade_price, fundamental_ticks, revenue, earnings, book_value, company_cash, debt = simulation.run()

trade_counts = {}
for trade in exchange.trade_history:
    trade_counts[trade.buy_trader_id] = trade_counts.get(trade.buy_trader_id, 0) + 1
    trade_counts[trade.sell_trader_id] = trade_counts.get(trade.sell_trader_id, 0) + 1

pairs = defaultdict(int)

final_price = exchange.get_last_trade_price(company.symbol)
if final_price is None:
    final_price = company.fundamental_value

for trader in traders:
    cancelled_orders = exchange.cancel_trader_orders(trader.trader_id)
    for order in cancelled_orders:
        if order.side == Side.BUY:
            if order.reserved_cash > 0:
                trader.money += order.reserved_cash
                order.reserved_cash = 0.0
            else:
                trader.money += order.price * order.remaining_quantity
        else:
            if order.reserved_shares > 0:
                trader.shares += order.reserved_shares
                order.reserved_shares = 0
            else:
                trader.shares += order.remaining_quantity

pnl_stats = []
for trader in traders:
    initial_value = initial_portfolio_values[trader.trader_id]
    final_value = trader.money + trader.shares * final_price
    pnl = final_value - initial_value
    return_pct = (pnl / initial_value) * 100 if initial_value > 0 else 0
    pnl_stats.append({
        "name": trader.name,
        "type": type(trader).__name__,
        "initial_value": initial_value,
        "final_value": final_value,
        "pnl": pnl,
        "return_pct": return_pct,
        "cash": trader.money,
        "shares": trader.shares,
        "trades": trade_counts.get(trader.trader_id, 0),
    })

for trade in exchange.trade_history:
    buyer = type(simulation.trader_map[trade.buy_trader_id]).__name__
    seller = type(simulation.trader_map[trade.sell_trader_id]).__name__
    key = tuple(sorted((buyer, seller)))
    pairs[key] += 1

for pair, count in sorted(pairs.items(), key=lambda x: x[1], reverse=True):
    print(pair, count)

trade_minutes = [trade.tick for trade in exchange.trade_history]
trade_hours = [m / 60.0 for m in trade_minutes]
trade_days_axis = [m / float(MINUTES_PER_DAY) for m in trade_minutes]
trade_prices = [trade.price for trade in exchange.trade_history]

fund_hours = simulation.time_hours
fund_days_axis = simulation.time_days

event_counts = defaultdict(int)
for event in simulation.event_history:
    event_counts[event.source] += 1

final_total_mtm = sum(s["final_value"] for s in pnl_stats)
final_total_cash = sum(t.money for t in traders)
final_total_shares = sum(t.shares for t in traders)
cash_gap = final_total_cash - (initial_total_cash - simulation.total_fees)
share_gap = final_total_shares - initial_total_shares

print("\n========== MARKET DIAGNOSTICS ==========")
print(f"Symbol:         {company.symbol} ({company.name})")
print(f"Session:        09:30–16:00 ({MINUTES_PER_DAY} trading minutes/day)")
print(f"Duration:       {DAYS} trading days ({simulation.total_minutes:,} minutes)")
print(f"Initial FV:     {initial_fv:.4f}")
print(f"Final FV:       {company.fundamental_value:.4f}")
print(f"Last trade:     {final_price}")
print(f"Trades:         {len(exchange.trade_history)}")
print(f"Events:         {dict(event_counts)} (total {len(simulation.event_history)})")
print(f"Events/day:     {len(simulation.event_history) / max(DAYS, 1):.1f}")
print(f"Total fees:     ${simulation.total_fees:,.2f}")
print(f"Initial MTM:    ${initial_total_mtm:,.2f}")
print(f"Final MTM:      ${final_total_mtm:,.2f}")
print(f"Cash conserv:   gap=${cash_gap:,.4f}")
print(f"Share conserv:  gap={share_gap}")

print("\n========== TRADER P&L ==========")
for stats in sorted(pnl_stats, key=lambda x: x["pnl"], reverse=True):
    print(
        f"{stats['name']:18} "
        f"{stats['type']:20} "
        f"P&L: ${stats['pnl']:>10,.2f} "
        f"Return: {stats['return_pct']:>7.2f}% "
        f"Trades: {stats['trades']}"
    )

type_stats = defaultdict(list)
for stats in pnl_stats:
    type_stats[stats["type"]].append(stats)

print("\n========== P&L BY STRATEGY ==========")
for trader_type, stats_list in sorted(type_stats.items()):
    average_pnl = sum(s["pnl"] for s in stats_list) / len(stats_list)
    average_return = sum(s["return_pct"] for s in stats_list) / len(stats_list)
    total_trades = sum(s["trades"] for s in stats_list)
    print(
        f"{trader_type:20} "
        f"Traders: {len(stats_list):3} "
        f"Avg P&L: ${average_pnl:>10,.2f} "
        f"Avg Return: {average_return:>7.2f}% "
        f"Trades: {total_trades:,}"
    )

plt.figure(figsize=(15, 7))
plt.plot(trade_days_axis, trade_prices, color="tab:blue", linewidth=0.8, label="Trade Price")
plt.plot(
    fund_days_axis,
    fundamental_price,
    color="tab:red",
    linewidth=2,
    linestyle="--",
    label="Fundamental Value",
)
plt.title(f"{company.symbol}: Market Price vs Fundamental ({DAYS} trading days)")
plt.xlabel("Trading Days")
plt.ylabel("Price")
plt.grid(alpha=0.3)
plt.legend()
plt.tight_layout()
plt.show()
