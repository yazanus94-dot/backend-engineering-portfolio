"""
LEGACY VERSION — intentionally preserved as-is (not fixed) to document the
starting point for the refactor. See CHANGELOG.md for the full list of
bugs found here and the performance numbers before/after.

This simulates a realistic situation: inheriting an existing log-analysis
script and being asked to fix its bugs and improve its performance before
extending it further.

Do not use this module in the actual pipeline — use
`refactored_log_analyzer.py` instead. Kept only for comparison.
"""


def find_duplicate_events(events, window_seconds=5):
    """Find pairs of events from the SAME user, with the SAME event name,
    that occur within `window_seconds` of each other (likely duplicate
    submissions, e.g. a double-clicked button).

    BUG #1 (see CHANGELOG): event-name comparison is case-sensitive, so
    "Login" and "login" are not recognized as the same event, even though
    upstream data is inconsistently cased.

    BUG #2 (see CHANGELOG): the O(n^2) nested-loop comparison below
    becomes impractically slow on large logs (see benchmarks/).
    """
    duplicates = []
    for i in range(len(events)):
        for j in range(i + 1, len(events)):
            e1, e2 = events[i], events[j]
            if e1["user_id"] != e2["user_id"]:
                continue
            if e1["event"] != e2["event"]:  # BUG #1: case-sensitive
                continue
            if abs(e1["timestamp"] - e2["timestamp"]) <= window_seconds:
                duplicates.append((e1, e2))
    return duplicates


def group_into_sessions(events, gap_threshold_seconds=1800, _cache={}):
    """Group a single user's chronological events into sessions, where a
    new session starts after a gap of more than `gap_threshold_seconds`.

    BUG #3 (see CHANGELOG): uses a mutable default argument (`_cache={}`)
    as memoization, which persists across calls and silently returns
    stale results for a user_id seen in a previous call.

    BUG #4 (see CHANGELOG): off-by-one in the gap comparison — uses `>=`
    instead of `>`, so an event exactly `gap_threshold_seconds` after the
    previous one incorrectly starts a new session.
    """
    user_id = events[0]["user_id"] if events else None
    if user_id in _cache:
        return _cache[user_id]

    sessions = []
    current = []
    for event in sorted(events, key=lambda e: e["timestamp"]):
        if not current:
            current.append(event)
            continue
        gap = event["timestamp"] - current[-1]["timestamp"]
        if gap >= gap_threshold_seconds:  # BUG #4: should be strictly >
            sessions.append(current)
            current = [event]
        else:
            current.append(event)
    if current:
        sessions.append(current)

    _cache[user_id] = sessions
    return sessions


def top_active_users(events, n=5):
    """Return the n most active users by event count."""
    counts = {}
    for e in events:
        counts[e["user_id"]] = counts.get(e["user_id"], 0) + 1
    # BUG #5 (see CHANGELOG): ties are broken arbitrarily by dict
    # iteration order rather than deterministically (e.g. by user_id),
    # so results can be inconsistent between runs/Python versions.
    return sorted(counts.items(), key=lambda kv: kv[1], reverse=True)[:n]
