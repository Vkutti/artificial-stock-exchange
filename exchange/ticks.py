"""US-equity-style price grid helpers (default $0.01 above $1)."""

DEFAULT_TICK_SIZE = 0.01


def round_to_tick(price, tick_size=DEFAULT_TICK_SIZE):
    """Snap a price to the nearest tick. Prices are floored at one tick."""
    if tick_size is None or tick_size <= 0:
        raise ValueError("tick_size must be positive")
    if price is None:
        raise ValueError("price required")
    ticks = round(float(price) / tick_size)
    snapped = ticks * tick_size
    # Avoid binary float noise (e.g. 10.1000000001)
    decimals = max(0, len(str(tick_size).rstrip("0").split(".")[-1]) if "." in str(tick_size) else 0)
    snapped = round(snapped, decimals + 2)
    return max(tick_size, snapped)


def spread_from_bps(mid, spread_bps, tick_size=DEFAULT_TICK_SIZE, min_ticks=1, max_bps=150.0):
    """Convert a mid and spread in bps to an absolute dollar half-spread*2 width, tick-snapped."""
    if mid is None or mid <= 0:
        mid = 1.0
    bps = max(0.0, min(float(max_bps), float(spread_bps)))
    width = mid * (bps / 10000.0)
    floor = tick_size * max(1, int(min_ticks))
    width = max(floor, width)
    return round_to_tick(width, tick_size)
