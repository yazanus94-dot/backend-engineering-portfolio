"""
REFACTORED VERSION — fixes all 5 bugs documented in CHANGELOG.md and
replaces the O(n^2) duplicate-detection algorithm with an O(n log n)
sort-and-sweep approach. See benchmarks/run_benchmarks.py for measured
before/after performance.
"""
from __future__ import annotations
from typing import Optional


def find_duplicate_events(events: list[dict], window_seconds: float = 5) -> list[tuple[dict, dict]]:
    """Find pairs of events from the same user, with the same event name
    (case-insensitively), occurring within `window_seconds` of each other.

    Fix for BUG #1: event names are normalized (lowercased + stripped)
    before comparison.

    Fix for BUG #2: instead of comparing every pair of events (O(n^2)),
    group events by (user_id, normalized_event_name) — only events that
    could possibly match share a group — then within each small group,
    sort by timestamp and sweep with a sliding window. This is
    O(n log n) overall (dominated by the per-group sort), and in
    practice far faster since groups are small relative to n.
    """
    groups: dict[tuple, list[dict]] = {}
    for e in events:
        key = (e["user_id"], e["event"].strip().lower())
        groups.setdefault(key, []).append(e)

    duplicates = []
    for group in groups.values():
        if len(group) < 2:
            continue
        group_sorted = sorted(group, key=lambda e: e["timestamp"])
        window_start = 0
        for i in range(1, len(group_sorted)):
            while group_sorted[i]["timestamp"] - group_sorted[window_start]["timestamp"] > window_seconds:
                window_start += 1
            for j in range(window_start, i):
                duplicates.append((group_sorted[j], group_sorted[i]))

    return duplicates


def group_into_sessions(events: list[dict], gap_threshold_seconds: float = 1800) -> list[list[dict]]:
    """Group a single user's chronological events into sessions, where a
    new session starts after a gap of STRICTLY MORE than
    `gap_threshold_seconds`.

    Fix for BUG #3: no mutable-default-argument cache. Memoization, if
    needed, is the caller's responsibility (explicit > implicit) — this
    function is now a pure function of its inputs.

    Fix for BUG #4: gap comparison uses `>` (strict), not `>=`, so an
    event exactly at the threshold stays in the same session.
    """
    if not events:
        return []

    sessions: list[list[dict]] = []
    current: list[dict] = []
    for event in sorted(events, key=lambda e: e["timestamp"]):
        if not current:
            current.append(event)
            continue
        gap = event["timestamp"] - current[-1]["timestamp"]
        if gap > gap_threshold_seconds:  # fixed: strictly greater than
            sessions.append(current)
            current = [event]
        else:
            current.append(event)
    if current:
        sessions.append(current)

    return sessions


def top_active_users(events: list[dict], n: int = 5) -> list[tuple]:
    """Return the n most active users by event count.

    Fix for BUG #5: ties are broken deterministically by user_id
    (ascending) after sorting by count (descending), so results are
    stable and reproducible across runs.
    """
    counts: dict = {}
    for e in events:
        counts[e["user_id"]] = counts.get(e["user_id"], 0) + 1

    return sorted(counts.items(), key=lambda kv: (-kv[1], str(kv[0])))[:n]
