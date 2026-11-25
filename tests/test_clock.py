from simulation.clock import SimClock, MINUTES_PER_DAY, OPEN_MINUTE, CLOSE_MINUTE


def test_minutes_per_day_constant():
    assert MINUTES_PER_DAY == 390
    assert CLOSE_MINUTE - OPEN_MINUTE == 390


def test_two_days_total_minutes():
    assert SimClock.total_minutes(2) == 780


def test_day_and_session_wrap():
    clock = SimClock(0)
    assert clock.day == 0
    assert clock.session_minute == 0
    assert clock.label() == "Day 1 09:30"
    assert clock.is_open

    clock.advance_to(389)
    assert clock.day == 0
    assert clock.is_end_of_day
    assert clock.label() == "Day 1 15:59"

    clock.advance_to(390)
    assert clock.day == 1
    assert clock.session_minute == 0
    assert clock.label() == "Day 2 09:30"


def test_hours_and_days_axes():
    clock = SimClock(195)  # halfway through day 1
    assert abs(clock.to_hours() - 3.25) < 1e-9
    assert abs(clock.to_days() - 0.5) < 1e-9
