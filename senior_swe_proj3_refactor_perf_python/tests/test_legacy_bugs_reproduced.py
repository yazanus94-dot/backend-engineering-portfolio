"""
Demonstrates that each bug listed in CHANGELOG.md is REAL and
reproducible against the legacy module — i.e. these tests are expected
to show the legacy module failing/misbehaving. This is the evidence
behind the changelog's bug list, not just a description of it.

Run: python -m unittest tests.test_legacy_bugs_reproduced -v
"""
import sys
import os
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import legacy_log_analyzer as legacy  # noqa: E402


class LegacyBug1CaseSensitivity(unittest.TestCase):
    def test_bug1_case_sensitive_duplicate_missed(self):
        """BUG #1: 'Login' and 'login' should be recognized as the same
        event but the legacy code misses this duplicate."""
        events = [
            {"user_id": 1, "event": "Login", "timestamp": 100},
            {"user_id": 1, "event": "login", "timestamp": 101},
        ]
        dupes = legacy.find_duplicate_events(events, window_seconds=5)
        self.assertEqual(len(dupes), 0, "legacy code incorrectly misses this case-variant duplicate")


class LegacyBug3MutableDefaultCache(unittest.TestCase):
    def test_bug3_stale_cache_across_calls(self):
        """BUG #3: a later call with the same user_id wrongly reuses a
        cached result from an earlier, unrelated call."""
        events_a = [{"user_id": 1, "event": "click", "timestamp": 0}]
        events_b = [
            {"user_id": 1, "event": "click", "timestamp": 0},
            {"user_id": 1, "event": "click", "timestamp": 100},
        ]
        legacy.group_into_sessions(events_a)
        stale_result = legacy.group_into_sessions(events_b)
        self.assertEqual(
            len(stale_result[0]), 1,
            "legacy code incorrectly returns the cached 1-event result from "
            "events_a instead of correctly processing events_b's 2 events",
        )


class LegacyBug4OffByOne(unittest.TestCase):
    def test_bug4_gap_exactly_at_threshold_incorrectly_splits(self):
        """BUG #4: a gap of EXACTLY the threshold should stay in the same
        session, but the legacy code splits it into two."""
        events = [
            {"user_id": 99, "event": "click", "timestamp": 0},
            {"user_id": 99, "event": "click", "timestamp": 1800},
        ]
        sessions = legacy.group_into_sessions(events, gap_threshold_seconds=1800)
        self.assertEqual(
            len(sessions), 2,
            "legacy code incorrectly splits into 2 sessions at exactly the threshold",
        )


if __name__ == "__main__":
    unittest.main()
