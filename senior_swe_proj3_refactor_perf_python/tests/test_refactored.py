"""
Tests for the REFACTORED module only — these encode the correct,
intended behavior. The legacy module is deliberately NOT held to these
tests (several would fail against it; that's the point, see CHANGELOG.md
and test_legacy_bugs_reproduced.py which demonstrates exactly that).
"""
import sys
import os
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from refactored_log_analyzer import (  # noqa: E402
    find_duplicate_events, group_into_sessions, top_active_users,
)


class FindDuplicateEventsTest(unittest.TestCase):
    def test_case_insensitive_match(self):
        events = [
            {"user_id": 1, "event": "Login", "timestamp": 100},
            {"user_id": 1, "event": "login", "timestamp": 102},
        ]
        dupes = find_duplicate_events(events, window_seconds=5)
        self.assertEqual(len(dupes), 1)

    def test_different_users_not_matched(self):
        events = [
            {"user_id": 1, "event": "login", "timestamp": 100},
            {"user_id": 2, "event": "login", "timestamp": 101},
        ]
        self.assertEqual(find_duplicate_events(events), [])

    def test_outside_window_not_matched(self):
        events = [
            {"user_id": 1, "event": "login", "timestamp": 100},
            {"user_id": 1, "event": "login", "timestamp": 200},
        ]
        self.assertEqual(find_duplicate_events(events, window_seconds=5), [])

    def test_different_event_names_not_matched(self):
        events = [
            {"user_id": 1, "event": "login", "timestamp": 100},
            {"user_id": 1, "event": "logout", "timestamp": 101},
        ]
        self.assertEqual(find_duplicate_events(events), [])

    def test_multiple_duplicates_in_window(self):
        events = [
            {"user_id": 1, "event": "click", "timestamp": 100},
            {"user_id": 1, "event": "click", "timestamp": 101},
            {"user_id": 1, "event": "click", "timestamp": 102},
        ]
        # 3 events within window of each other -> 3 pairs: (0,1),(0,2),(1,2)
        dupes = find_duplicate_events(events, window_seconds=5)
        self.assertEqual(len(dupes), 3)

    def test_matches_naive_on_quadratic_reference(self):
        """Cross-check the optimized grouping+sweep approach against a
        brute-force O(n^2) reference implementation on random data, to
        make sure the optimization didn't change the result set."""
        from data_generator import generate_events

        def naive_reference(events, window_seconds):
            out = []
            for i in range(len(events)):
                for j in range(i + 1, len(events)):
                    e1, e2 = events[i], events[j]
                    if e1["user_id"] != e2["user_id"]:
                        continue
                    if e1["event"].strip().lower() != e2["event"].strip().lower():
                        continue
                    if abs(e1["timestamp"] - e2["timestamp"]) <= window_seconds:
                        out.append((e1, e2))
            return out

        events = generate_events(300, seed=1)
        fast_count = len(find_duplicate_events(events, window_seconds=5))
        naive_count = len(naive_reference(events, window_seconds=5))
        self.assertEqual(fast_count, naive_count)


class GroupIntoSessionsTest(unittest.TestCase):
    def test_single_session_within_gap(self):
        events = [
            {"user_id": 1, "event": "click", "timestamp": 0},
            {"user_id": 1, "event": "click", "timestamp": 100},
            {"user_id": 1, "event": "click", "timestamp": 200},
        ]
        sessions = group_into_sessions(events, gap_threshold_seconds=1800)
        self.assertEqual(len(sessions), 1)
        self.assertEqual(len(sessions[0]), 3)

    def test_splits_on_large_gap(self):
        events = [
            {"user_id": 1, "event": "click", "timestamp": 0},
            {"user_id": 1, "event": "click", "timestamp": 5000},
        ]
        sessions = group_into_sessions(events, gap_threshold_seconds=1800)
        self.assertEqual(len(sessions), 2)

    def test_gap_exactly_at_threshold_stays_in_same_session(self):
        """Regression test for the off-by-one bug (legacy BUG #4): a gap
        of EXACTLY the threshold should NOT start a new session."""
        events = [
            {"user_id": 1, "event": "click", "timestamp": 0},
            {"user_id": 1, "event": "click", "timestamp": 1800},
        ]
        sessions = group_into_sessions(events, gap_threshold_seconds=1800)
        self.assertEqual(len(sessions), 1)

    def test_no_cross_call_state_leakage(self):
        """Regression test for the mutable-default-argument bug (legacy
        BUG #3): calling the function for one user must not affect the
        result for a different call with the same user_id value later."""
        events_a = [{"user_id": 1, "event": "click", "timestamp": 0}]
        events_b = [
            {"user_id": 1, "event": "click", "timestamp": 0},
            {"user_id": 1, "event": "click", "timestamp": 100},
        ]
        group_into_sessions(events_a)
        result_b = group_into_sessions(events_b)
        self.assertEqual(len(result_b[0]), 2)  # not stale from events_a

    def test_empty_input(self):
        self.assertEqual(group_into_sessions([]), [])

    def test_unsorted_input_is_sorted_internally(self):
        events = [
            {"user_id": 1, "event": "click", "timestamp": 200},
            {"user_id": 1, "event": "click", "timestamp": 0},
            {"user_id": 1, "event": "click", "timestamp": 100},
        ]
        sessions = group_into_sessions(events, gap_threshold_seconds=1800)
        timestamps = [e["timestamp"] for e in sessions[0]]
        self.assertEqual(timestamps, sorted(timestamps))


class TopActiveUsersTest(unittest.TestCase):
    def test_basic_ranking(self):
        events = (
            [{"user_id": 1, "event": "x", "timestamp": i} for i in range(3)]
            + [{"user_id": 2, "event": "x", "timestamp": i} for i in range(5)]
        )
        top = top_active_users(events, n=2)
        self.assertEqual(top[0], (2, 5))
        self.assertEqual(top[1], (1, 3))

    def test_tie_broken_deterministically_by_user_id(self):
        """Regression test for the nondeterministic-tie-break bug (legacy
        BUG #5): with equal counts, lower user_id must sort first,
        consistently."""
        events = (
            [{"user_id": 30, "event": "x", "timestamp": 0}]
            + [{"user_id": 10, "event": "x", "timestamp": 0}]
            + [{"user_id": 20, "event": "x", "timestamp": 0}]
        )
        for _ in range(5):  # run multiple times to rule out flakiness
            top = top_active_users(events, n=3)
            self.assertEqual([uid for uid, _ in top], [10, 20, 30])

    def test_n_larger_than_user_count(self):
        events = [{"user_id": 1, "event": "x", "timestamp": 0}]
        top = top_active_users(events, n=10)
        self.assertEqual(len(top), 1)


if __name__ == "__main__":
    unittest.main()
