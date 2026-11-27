"""Multi-seed stylized-fact and strategy P&L report."""

import argparse
import math
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from main import run_simulation


def excess_kurtosis(x):
    x = np.asarray(x, dtype=float)
    if len(x) < 4:
        return float("nan")
    m = x.mean()
    m2 = np.mean((x - m) ** 2)
    if m2 <= 0:
        return float("nan")
    m4 = np.mean((x - m) ** 4)
    return float(m4 / (m2 ** 2) - 3.0)


def acf1(x):
    x = np.asarray(x, dtype=float)
    if len(x) < 3:
        return float("nan")
    x0 = x[:-1] - x[:-1].mean()
    x1 = x[1:] - x[1:].mean()
    denom = np.sqrt(np.sum(x0 ** 2) * np.sum(x1 ** 2))
    if denom <= 0:
        return float("nan")
    return float(np.sum(x0 * x1) / denom)


def mean_ci(values, z=1.96):
    arr = np.asarray(values, dtype=float)
    n = len(arr)
    if n == 0:
        return float("nan"), float("nan"), float("nan")
    mu = float(arr.mean())
    se = float(arr.std(ddof=1) / math.sqrt(n)) if n > 1 else 0.0
    return mu, mu - z * se, mu + z * se


def run_report(seeds, days):
    strategy_returns = defaultdict(list)
    kurtoses = []
    ret_acf = []
    sq_acf = []
    vols = []

    for seed in seeds:
        print(f"\n--- seed {seed} ---")
        result = run_simulation(days=days, seed=seed, plot=False, verbose=False)
        rets = result["daily_returns"]
        kurtoses.append(excess_kurtosis(rets))
        ret_acf.append(acf1(rets))
        sq_acf.append(acf1(rets ** 2))
        vols.append(result["ann_vol"])
        for ttype, stats_list in result["type_stats"].items():
            avg_ret = sum(s["return_pct"] for s in stats_list) / len(stats_list)
            strategy_returns[ttype].append(avg_ret)

    print("\n========== STYLIZED FACTS ==========")
    print(f"Seeds: {len(seeds)}  Days: {days}")
    mu, lo, hi = mean_ci(kurtoses)
    print(f"Excess kurtosis:     {mu:7.3f}  CI [{lo:7.3f}, {hi:7.3f}]")
    mu, lo, hi = mean_ci(ret_acf)
    print(f"Return AC(1):        {mu:7.3f}  CI [{lo:7.3f}, {hi:7.3f}]")
    mu, lo, hi = mean_ci(sq_acf)
    print(f"Squared-ret AC(1):   {mu:7.3f}  CI [{lo:7.3f}, {hi:7.3f}]")
    mu, lo, hi = mean_ci(vols)
    print(f"Ann. vol:            {mu*100:6.2f}%  CI [{lo*100:6.2f}%, {hi*100:6.2f}%]")

    print("\n========== STRATEGY RETURN % (mean ± 95% CI) ==========")
    for ttype in sorted(strategy_returns):
        mu, lo, hi = mean_ci(strategy_returns[ttype])
        print(f"{ttype:20} {mu:7.2f}%  CI [{lo:7.2f}%, {hi:7.2f}%]")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--seeds", type=int, default=30)
    parser.add_argument("--days", type=int, default=21)
    parser.add_argument("--start-seed", type=int, default=1)
    args = parser.parse_args()
    seeds = list(range(args.start_seed, args.start_seed + args.seeds))
    run_report(seeds, args.days)


if __name__ == "__main__":
    main()
