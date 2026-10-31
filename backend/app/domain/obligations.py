"""Pure obligation rules: no DB, no clock reads. Callers pass `now`."""
from datetime import datetime, timedelta

DUE_SOON_DAYS = 30


def obligation_status(*, due_at: datetime, now: datetime, fulfilled: bool = False,
                      waived: bool = False, paused: bool = False,
                      due_soon_days: int = DUE_SOON_DAYS) -> str:
    if fulfilled:
        return "FULFILLED"
    if waived:
        return "WAIVED"
    if paused:
        return "PAUSED"
    if now > due_at:
        return "OVERDUE"
    if due_at - now <= timedelta(days=due_soon_days):
        return "DUE_SOON"
    return "UPCOMING"


def step_time(due_at: datetime, step: dict) -> datetime:
    return due_at + timedelta(days=step["days_offset"])


def steps_to_fire(*, now: datetime, due_at: datetime, ladder: list[dict],
                  logged_keys: set[str]) -> tuple[dict | None, list[dict]]:
    """D-09: only the latest due, unlogged step fires; earlier due, unlogged ones are skipped.

    `logged_keys` holds every step already in the alert log (SENT or SKIPPED), so reruns are no-ops.
    """
    due = sorted(
        (s for s in ladder if s["key"] not in logged_keys and step_time(due_at, s) <= now),
        key=lambda s: s["days_offset"],
    )
    return (due[-1], due[:-1]) if due else (None, [])
