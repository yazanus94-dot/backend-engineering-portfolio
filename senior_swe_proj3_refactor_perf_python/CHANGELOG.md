# Changelog: Legacy Log Analyzer Refactor

Simulates inheriting an existing log-analysis script with real bugs and
a performance problem, then fixing and optimizing it — the exact kind of
work this project is meant to demonstrate: bug fixing, codebase
refactoring, and performance optimization on an existing codebase rather
than greenfield code.

## Bugs found and fixed

Each bug below has a corresponding regression test in
`tests/test_refactored.py` (proving the fix) and a reproduction test in
`tests/test_legacy_bugs_reproduced.py` (proving the bug was real in the
legacy code, not just a description).

1. **Case-sensitive duplicate-event matching** (`find_duplicate_events`).
   `"Login"` and `"login"` were treated as different events, so real
   duplicate submissions with inconsistent casing were missed entirely.
   **Fix:** normalize event names (strip + lowercase) before comparison.

2. **O(n²) duplicate detection.** Every event was compared against every
   other event. **Fix:** group events by `(user_id, normalized_event)` —
   only events in the same group can ever match — then sort each small
   group by timestamp and sweep with a sliding window. O(n log n)
   overall. See `benchmarks/results.csv` for measured speedup (up to
   **326x faster** at n=4216 events in this run).

3. **Mutable default argument used as a cache**
   (`group_into_sessions(events, ..., _cache={})`). Because default
   argument values are created once, at function-definition time, and
   reused across all calls, a later call for the same `user_id` silently
   returned a stale, incorrect result from an earlier, unrelated call.
   **Fix:** removed the implicit cache entirely — the function is now
   pure (same inputs always produce the same output), and caching, if
   needed, is left as an explicit decision for the caller.

4. **Off-by-one in session-gap comparison.** Used `gap >= threshold`
   instead of `gap > threshold`, so an event occurring at *exactly* the
   gap threshold incorrectly started a new session instead of staying in
   the current one. **Fix:** corrected to strict `>`.

5. **Nondeterministic tie-breaking** in `top_active_users`. Users with
   equal event counts were ordered by dict iteration order, which is
   insertion-order-dependent and not guaranteed to be stable or
   meaningful across different input orderings. **Fix:** ties are now
   broken deterministically by ascending `user_id`.

## Performance: before vs. after

| n_events | legacy O(n²) | refactored O(n log n) | speedup |
|---:|---:|---:|---:|
| 216 | 2.2 ms | 0.12 ms | 18.2x |
| 531 | 12.3 ms | 0.31 ms | 39.4x |
| 1,056 | 63.8 ms | 0.62 ms | 102.7x |
| 2,109 | 264.8 ms | 1.22 ms | 216.8x |
| 4,216 | 905.4 ms | 2.78 ms | **326.3x** |

The speedup grows with input size, as expected for O(n²) vs O(n log n) —
reproduce with `python benchmarks/run_benchmarks.py`.
