"""
Benchmarks legacy (O(n^2)) vs. refactored (O(n log n)) duplicate-event
detection across input sizes, to measure the real performance win from
the refactor (not just assert it).

Run: python benchmarks/run_benchmarks.py
"""
import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import legacy_log_analyzer as legacy  # noqa: E402
import refactored_log_analyzer as refactored  # noqa: E402
from data_generator import generate_events  # noqa: E402


def timeit(fn, *args, repeats=1):
    best = float("inf")
    for _ in range(repeats):
        start = time.perf_counter()
        fn(*args)
        best = min(best, time.perf_counter() - start)
    return best


def main():
    sizes = [200, 500, 1000, 2000, 4000]
    print(f"{'n_events':>10} {'legacy O(n^2) (s)':>20} {'refactored O(n log n) (s)':>28} {'speedup':>10}")
    print("-" * 72)

    rows = []
    for n in sizes:
        events = generate_events(n, seed=1)
        legacy_time = timeit(legacy.find_duplicate_events, events, 5, repeats=1)
        refactored_time = timeit(refactored.find_duplicate_events, events, 5, repeats=3)
        speedup = legacy_time / refactored_time if refactored_time > 0 else float("inf")
        rows.append((len(events), legacy_time, refactored_time, speedup))
        print(f"{len(events):>10} {legacy_time:>20.6f} {refactored_time:>28.6f} {speedup:>9.1f}x")

    with open(os.path.join(os.path.dirname(__file__), "results.csv"), "w") as f:
        f.write("n_events,legacy_seconds,refactored_seconds,speedup\n")
        for n, lt, rt, sp in rows:
            f.write(f"{n},{lt:.6f},{rt:.6f},{sp:.2f}\n")
    print("\nSaved -> benchmarks/results.csv")


if __name__ == "__main__":
    main()
