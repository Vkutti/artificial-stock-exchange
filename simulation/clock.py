"""Trading-minute calendar clock (NYSE-style session).

1 simulation tick = 1 trading minute.
Session: 09:30–16:00 → 390 minutes per day.
"""

MINUTES_PER_DAY = 390
OPEN_MINUTE = 9 * 60 + 30   # 09:30 from midnight
CLOSE_MINUTE = 16 * 60      # 16:00 from midnight


class SimClock:
    def __init__(self, minute_index=0):
        self.minute_index = int(minute_index)

    def advance_to(self, minute_index):
        self.minute_index = int(minute_index)

    @property
    def day(self):
        """0-based trading day index."""
        return self.minute_index // MINUTES_PER_DAY

    @property
    def session_minute(self):
        """Minutes since today's open (0..389)."""
        return self.minute_index % MINUTES_PER_DAY

    @property
    def clock_minute(self):
        """Minutes since midnight on the wall clock."""
        return OPEN_MINUTE + self.session_minute

    @property
    def hour(self):
        return self.clock_minute // 60

    @property
    def minute(self):
        return self.clock_minute % 60

    @property
    def is_open(self):
        return OPEN_MINUTE <= self.clock_minute < CLOSE_MINUTE

    @property
    def is_end_of_day(self):
        return self.session_minute == MINUTES_PER_DAY - 1

    def label(self):
        return f"Day {self.day + 1} {self.hour:02d}:{self.minute:02d}"

    def to_hours(self):
        """Trading hours elapsed from sim start (continuous trading-time axis)."""
        return self.minute_index / 60.0

    def to_days(self):
        """Trading days elapsed from sim start (fractional)."""
        return self.minute_index / float(MINUTES_PER_DAY)

    @staticmethod
    def total_minutes(days):
        return int(days) * MINUTES_PER_DAY

    @staticmethod
    def from_minute_index(minute_index):
        return SimClock(minute_index)

    def __repr__(self):
        return f"SimClock({self.label()}, idx={self.minute_index})"
