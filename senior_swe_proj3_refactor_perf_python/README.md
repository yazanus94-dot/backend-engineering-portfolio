# Legacy Codebase Refactor & Performance Optimization

Personal portfolio project simulating a common real-world task: inheriting
an existing, buggy, slow script and fixing/optimizing it with evidence,
not just rewriting it from scratch and claiming it's better.

## Why this project

Most "algorithms" portfolio pieces show new code being written from a
blank file. This one instead demonstrates the skills a role actually
needs day-to-day on an existing codebase: **finding real bugs in working
code, proving they exist, fixing them without breaking anything else,
and measuring the performance impact of an optimization** — see
`CHANGELOG.md` for the full bug list and before/after benchmark numbers.

## Structure

- **`src/legacy_log_analyzer.py`** — the "inherited" version, kept
  unmodified (bugs and all) for comparison. Analyzes a stream of
  (user_id, event, timestamp) log entries: finds likely-duplicate
  events, groups events into user sessions, and ranks the most active
  users. Contains 5 real, reproducible bugs (see `CHANGELOG.md`) and an
  O(n²) duplicate-detection algorithm.
- **`src/refactored_log_analyzer.py`** — same functionality, all 5 bugs
  fixed, and duplicate detection rewritten to O(n log n).
- **`tests/test_legacy_bugs_reproduced.py`** — proves each legacy bug is
  real by reproducing it against the unmodified legacy code.
- **`tests/test_refactored.py`** — 18 tests total (including the 3
  legacy-bug-reproduction tests) verifying the refactored version is
  correct, including explicit regression tests for each fixed bug and a
  cross-check of the optimized algorithm against a brute-force reference
  implementation on random data.
- **`benchmarks/run_benchmarks.py`** — times legacy vs. refactored
  duplicate detection across input sizes; results in `benchmarks/results.csv`.

## Run it

```bash
# tests (18 tests — correctness + legacy bug reproduction)
python -m unittest discover -s tests -v

# benchmark (legacy vs refactored performance)
python benchmarks/run_benchmarks.py
```

No external dependencies — pure standard library.

## Headline result

Refactored duplicate-detection is **up to 326x faster** than the legacy
O(n²) version at 4,216 events, with the speedup growing as input size
grows — see `CHANGELOG.md` for the full table and methodology.
