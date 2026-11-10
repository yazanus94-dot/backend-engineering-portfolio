"""
Benchmarks the three sorting implementations against Python's built-in
Timsort (sorted()) across input sizes and distributions, to make the
complexity differences concrete rather than theoretical.

Run: python benchmarks/run_benchmarks.py
"""
import os
import random
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from sorting import quicksort, mergesort, insertion_sort  # noqa: E402


def timeit(fn, data, repeats=3):
    best = float("inf")
    for _ in range(repeats):
        start = time.perf_counter()
        fn(data)
        best = min(best, time.perf_counter() - start)
    return best


def make_dataset(n, kind, seed=0):
    rng = random.Random(seed)
    if kind == "random":
        return [rng.randint(-10**6, 10**6) for _ in range(n)]
    if kind == "sorted":
        return list(range(n))
    if kind == "reverse_sorted":
        return list(range(n, 0, -1))
    raise ValueError(kind)


def main():
    sizes = [100, 1000, 5000]
    kinds = ["random", "sorted", "reverse_sorted"]
    algorithms = {
        "insertion_sort (O(n^2))": insertion_sort,
        "quicksort (O(n log n) avg)": quicksort,
        "mergesort (O(n log n) worst-case)": mergesort,
        "builtin sorted() (Timsort)": sorted,
    }

    print(f"{'size':>6} {'input':>15} {'algorithm':35} {'time (s)':>10}")
    print("-" * 72)

    results = []
    for n in sizes:
        for kind in kinds:
            data = make_dataset(n, kind)
            for name, fn in algorithms.items():
                # skip insertion sort on large random inputs: O(n^2) makes
                # it impractically slow and the point (it's quadratic) is
                # already made at smaller sizes
                if "insertion" in name and n > 1000:
                    continue
                t = timeit(fn, data, repeats=3 if n <= 1000 else 1)
                results.append((n, kind, name, t))
                print(f"{n:>6} {kind:>15} {name:35} {t:>10.6f}")

    with open(os.path.join(os.path.dirname(__file__), "results.csv"), "w") as f:
        f.write("size,input_kind,algorithm,time_seconds\n")
        for n, kind, name, t in results:
            f.write(f"{n},{kind},{name},{t:.6f}\n")
    print("\nSaved -> benchmarks/results.csv")


if __name__ == "__main__":
    main()
