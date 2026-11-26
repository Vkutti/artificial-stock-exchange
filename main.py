from exchange.exchange import Exchange
from simulation.simulation import Simulation
from simulation.clock import MINUTES_PER_DAY
from company.economy import Economy

from traders.random_trader import RandomTrader
from traders.market_maker import MarketMaker
from traders.fair_value_trader import FairValueTrader
from traders.momentum_trader import MomentumTrader
from traders.persistent_trader import PersistentTrader
from traders.sentiment_trader import SentimentTrader
from traders.news_trader import NewsTrader
from traders.index_fund_trader import IndexFundTrader

from company.company import Company

import random
import math
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from collections import defaultdict

# DAYS = 1
DAYS = 5
# DAYS = 21
# DAYS = 63
# DAYS = 252

COMPANY_SPECS = [
    ("ABC Incorporated", "Technology", "ABC", 10000000, 2000000, 1000000, 3600000, 8000000),
    ("NexBank Corp", "Finance", "NBK", 12000000, 5000000, 900000, 4000000, 9000000),
    ("Helix Health", "Healthcare", "HLX", 8000000, 1500000, 700000, 3000000, 7000000),
]

exchange = Exchange()
economy = Economy(0.05)
companies = {}
for name, industry, symbol, money0, debt, earn, rev, book in COMPANY_SPECS:
    companies[symbol] = Company(
        name, industry, money0, debt, earn, rev, book, 1000000, 0.5, symbol=symbol
    )

primary = companies["ABC"]
symbols = list(companies.keys())

FIRST_NAMES = [
    "James", "Michael", "William", "David", "John", "Robert", "Joseph", "Thomas",
    "Charles", "Daniel", "Matthew", "Anthony", "Mark", "Donald", "Steven", "Paul",
    "Andrew", "Joshua", "Kenneth", "Kevin", "Brian", "George", "Edward", "Ronald",
    "Timothy", "Jason", "Jeffrey", "Ryan", "Jacob", "Nicholas", "Aiden", "Asher",
    "Cameron", "Cooper", "Damian", "Evan", "Felix", "Finn", "Graham", "Harrison",
    "Hudson", "Jasper", "Kai", "Landon", "Liam", "Mason", "Nathaniel", "Oliver",
    "Parker", "Preston", "Reid", "Rowan", "Silas", "Theo", "Tristan", "Wesley",
    "Wyatt", "Zane", "Kieran", "Emmett", "Austin", "Dylan", "Hunter", "Jordan",
    "Ethan", "Logan", "Noah", "Caleb", "Luke", "Connor", "Owen", "Eli", "Isaac",
    "Gabriel", "Julian", "Miles", "Dominic", "Vincent", "Victor", "Oscar", "Leon",
    "Joel", "Xavier", "Cole", "Blake", "Spencer", "Gavin", "Grant", "Trevor", "Max",
    "Benjamin", "Samuel", "Alexander", "Patrick", "Jack", "Nathan", "Justin", "Aaron",
    "Adam", "Christian", "Tyler", "Zachary", "Eric", "Brandon", "Jonathan", "Scott",
    "Gregory", "Frank", "Raymond", "Jerry", "Dennis", "Walter", "Henry", "Douglas",
    "Peter", "Harold", "Carl", "Arthur", "Lawrence", "Sean", "Elena", "Priya",
    "Marcus", "Sofia", "Nina", "Omar", "Iris", "Leo", "Ava", "Nora", "Hugo", "Clara",
    "Ivy", "Jude", "Vera", "Quinn", "Remy", "Sage", "Tess", "Wade", "Yuki", "Zoe",
    "Amir", "Bea", "Cody", "Drew", "Elle", "Faye", "Gus", "Hope", "Ian", "Jade",
    "Kyle", "Lana", "Moe", "Nell", "Orion", "Pax", "Rita", "Skye", "Troy", "Uma",
    "Vince", "Willa", "Xander", "Yael", "Zara", "Brooks", "Casey", "Devon", "Eden",
    "Finley", "Gray", "Harper", "Indigo", "Jules", "Kendall", "Lane", "Morgan",
    "Noel", "Oakley", "Peyton", "Reese", "Shannon", "Taylor", "Val", "Winter", "Ash",
    "Blair", "Dallas", "Emerson", "Frankie", "Hayden", "Jamie", "Kelly", "Marley",
    "Riley", "Sawyer", "Toby", "Alex", "Chris", "Sam", "Pat", "Robin", "Terry",
    "Kim", "Lee", "Tracy", "Dana", "Leslie", "Carey", "Adrian", "Sidney", "Bernie",
    "Jackie", "Ronnie", "Stevie", "Bill", "Ted", "Ned", "Fred", "Al", "Cal", "Sal",
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
    return random.randint(0, max(1, int(cash // 40)))


def assign(trader, symbol):
    trader.symbol = symbol
    return trader


money = [1000, 2000, 5000, 8000, 10000, 20000, 50000, 100000]
traders = []

for i, sym in enumerate(symbols):
    traders.append(assign(MarketMaker(next_name("MM", i), 250000, 12000, 0), sym))
    traders.append(assign(MarketMaker(next_name("MM", i + 10), 250000, 12000, 0), sym))
    traders.append(assign(MarketMaker(next_name("MM", i + 20), 250000, 12000, 0), sym))

for i in range(60):
    cash = random.choice(money)
    traders.append(assign(RandomTrader(next_name("RND", i), cash, starter_inventory(cash), 0), symbols[i % 3]))

for i in range(45):
    cash = random.choice(money)
    traders.append(assign(FairValueTrader(next_name("FV", i), cash, starter_inventory(cash), 0), symbols[i % 3]))

for i in range(30):
    cash = random.choice(money)
    traders.append(assign(MomentumTrader(next_name("MOM", i), cash, starter_inventory(cash), 0), symbols[i % 3]))

for i in range(24):
    cash = random.choice(money)
    traders.append(assign(PersistentTrader(next_name("PER", i), cash, starter_inventory(cash), 0), symbols[i % 3]))

for i in range(24):
    cash = random.choice(money)
    traders.append(assign(SentimentTrader(next_name("SENT", i), cash, starter_inventory(cash), 0), symbols[i % 3]))

for i in range(18):
    cash = random.choice(money)
    traders.append(assign(NewsTrader(next_name("NEWS", i), cash, starter_inventory(cash), 0), symbols[i % 3]))

for i in range(9):
    cash = random.choice(money)
    traders.append(assign(IndexFundTrader(next_name("IDX", i), cash * 2, starter_inventory(cash), 0), symbols[i % 3]))

assert len({t.name for t in traders}) == len(traders)

simulation = Simulation(
    exchange,
    traders,
    companies=companies,
    days=DAYS,
    verbose=False,
    fee_rate=0.001,
    playback_delay_sec=0.0,
    economy=economy,
    enable_auctions=True,
    enable_circuit_breakers=True,
)

initial_prices = {s: c.fundamental_value for s, c in companies.items()}
initial_fv = primary.fundamental_value
initial_total_cash = sum(t.money for t in traders)
initial_total_shares = sum(t.shares for t in traders)

initial_portfolio_values = {}
for trader in traders:
    px = initial_prices[trader.symbol]
    initial_portfolio_values[trader.trader_id] = trader.money + trader.shares * px

initial_total_mtm = sum(initial_portfolio_values.values())

bid_data, ask_data, mid_data, fundamental_price, spread, volume, last_trade_price, fundamental_ticks, revenue, earnings, book_value, company_cash, debt = simulation.run()

trade_counts = defaultdict(int)
for trade in exchange.trade_history:
    trade_counts[trade.buy_trader_id] += 1
    trade_counts[trade.sell_trader_id] += 1

pairs = defaultdict(int)
for trade in exchange.trade_history:
    buyer = type(simulation.trader_map[trade.buy_trader_id]).__name__
    seller = type(simulation.trader_map[trade.sell_trader_id]).__name__
    pairs[tuple(sorted((buyer, seller)))] += 1

for pair, count in sorted(pairs.items(), key=lambda x: x[1], reverse=True):
    print(pair, count)

final_prices = {}
for sym, comp in companies.items():
    px = exchange.get_last_trade_price(sym)
    final_prices[sym] = px if px is not None else comp.fundamental_value

pnl_stats = []
for trader in traders:
    px = final_prices[trader.symbol]
    initial_value = initial_portfolio_values[trader.trader_id]
    final_value = trader.money + trader.shares * px
    pnl = final_value - initial_value
    return_pct = (pnl / initial_value) * 100 if initial_value > 0 else 0
    pnl_stats.append({
        "name": trader.name,
        "type": type(trader).__name__,
        "symbol": trader.symbol,
        "initial_value": initial_value,
        "final_value": final_value,
        "pnl": pnl,
        "return_pct": return_pct,
        "trades": trade_counts.get(trader.trader_id, 0),
    })

primary_trades = [t for t in exchange.trade_history if (t.symbol or "ABC") == "ABC"]
trade_minutes = [t.tick for t in primary_trades]
trade_days_axis = [m / float(MINUTES_PER_DAY) for m in trade_minutes]
trade_prices = [t.price for t in primary_trades]
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
print(f"Symbols:        {', '.join(symbols)}")
print(f"Session:        09:30–16:00 ({MINUTES_PER_DAY} min/day)")
print(f"Duration:       {DAYS} trading days ({simulation.total_minutes:,} minutes)")
print(f"Primary:        ABC FV {initial_fv:.4f} -> {primary.fundamental_value:.4f}")
print(f"Last ABC:       {final_prices['ABC']}")
print(f"Trades:         {len(exchange.trade_history)}")
print(f"Auctions:       {len(simulation.auction_prints)}")
print(f"Halts:          {dict(simulation.halt_counts)}")
print(f"Events:         {dict(event_counts)} (total {len(simulation.event_history)})")
print(f"Rate:           {economy.risk_free_rate * 100:.2f}%")
print(f"Flow mult:      {economy.flow_multiplier:.2f}")
print(f"Total fees:     ${simulation.total_fees:,.2f}")
print(f"Initial MTM:    ${initial_total_mtm:,.2f}")
print(f"Final MTM:      ${final_total_mtm:,.2f}")
print(f"Cash conserv:   gap=${cash_gap:,.4f}")
print(f"Share conserv:  gap={share_gap}")

print("\n========== PER SYMBOL ==========")
for sym, comp in companies.items():
    n = sum(1 for t in exchange.trade_history if (t.symbol or primary.symbol) == sym)
    print(
        f"{sym}: FV {initial_prices[sym]:.2f}->{comp.fundamental_value:.2f} "
        f"last={final_prices[sym]} trades={n}"
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

eod_prices = []
if trade_minutes:
    day_buckets = defaultdict(list)
    for m, p in zip(trade_minutes, trade_prices):
        day_buckets[int(m // MINUTES_PER_DAY)].append(p)
    for d in range(DAYS):
        if d in day_buckets:
            eod_prices.append(day_buckets[d][-1])
        elif eod_prices:
            eod_prices.append(eod_prices[-1])
        else:
            eod_prices.append(float(initial_fv))
else:
    eod_prices = [float(initial_fv)] * DAYS

eod = np.asarray(eod_prices, dtype=float)
fv_series = np.asarray(fundamental_price, dtype=float)
daily_rets = np.diff(eod) / np.maximum(eod[:-1], 1e-9)
ann_vol = float(np.std(daily_rets) * math.sqrt(252)) if len(daily_rets) > 1 else 0.0
ann_ret = float(eod[-1] / eod[0] - 1.0) if eod[0] > 0 else 0.0
fv_ann_ret = float(fv_series[-1] / fv_series[0] - 1.0) if len(fv_series) and fv_series[0] > 0 else 0.0
max_dd = 0.0
peak = eod[0]
for px in eod:
    peak = max(peak, px)
    max_dd = min(max_dd, px / peak - 1.0)

spread_bps_samples = []
for b, a in zip(bid_data, ask_data):
    if b is not None and a is not None and a > 0 and b > 0:
        mid = 0.5 * (b + a)
        if mid > 0:
            spread_bps_samples.append((a - b) / mid * 10000.0)
avg_spread_bps = float(np.mean(spread_bps_samples)) if spread_bps_samples else float("nan")
news_trader_trades = sum(s["trades"] for s in pnl_stats if s["type"] == "NewsTrader")
trades_per_day = len(exchange.trade_history) / max(DAYS, 1)

print("\n========== YEAR REALISM CHECK ==========")
print(f"Price annual return:   {ann_ret * 100:>7.2f}%")
print(f"FV annual return:      {fv_ann_ret * 100:>7.2f}%")
print(f"Ann. daily vol:        {ann_vol * 100:>7.2f}%")
print(f"Max drawdown:          {max_dd * 100:>7.2f}%")
print(f"Avg spread (bps):      {avg_spread_bps:>7.1f}")
print(f"NewsTrader fills:      {news_trader_trades:>7d}")
print(f"Trades / day:          {trades_per_day:>7.1f}")
print(f"Auctions fired:        {len(simulation.auction_prints):>7d}")

checks = [
    ("FV return in [-20%, +40%]", -0.20 <= fv_ann_ret <= 0.40),
    ("Price vol in 15–60%", 0.15 <= ann_vol <= 0.60),
    ("Max DD milder than -80%", max_dd > -0.80),
    ("Avg spread 5–80 bps", 5.0 <= avg_spread_bps <= 80.0),
    ("NewsTrader traded", news_trader_trades > 0),
    ("Cash conservation", abs(cash_gap) < 1e-4),
    ("Share conservation", share_gap == 0),
    ("Some daily trading", trades_per_day >= 10),
    ("Auctions ran", len(simulation.auction_prints) > 0),
    ("No negative cash", all(t.money >= -1e-6 for t in traders)),
]
print("\n========== SANITY FLAGS ==========")
for label, ok in checks:
    print(f"{'PASS' if ok else 'FAIL':4}  {label}")

plot_path = os.path.join(os.path.dirname(__file__) or ".", f"year_run_{DAYS}d.png")
plt.figure(figsize=(15, 7))
plt.plot(trade_days_axis, trade_prices, color="tab:blue", linewidth=0.6, alpha=0.7, label="ABC Trade Price")
plt.plot(fund_days_axis, fundamental_price, color="tab:red", linewidth=2, linestyle="--", label="ABC Fundamental")
plt.title(f"ABC (+{len(symbols)-1} names): Price vs Fundamental ({DAYS} trading days)")
plt.xlabel("Trading Days")
plt.ylabel("Price")
plt.grid(alpha=0.3)
plt.legend()
plt.tight_layout()
plt.savefig(plot_path, dpi=140)
plt.close()
print(f"\nPlot saved: {plot_path}")
