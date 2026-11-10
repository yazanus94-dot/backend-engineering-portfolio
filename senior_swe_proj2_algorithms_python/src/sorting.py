"""
Classic sorting algorithms implemented from scratch, for complexity
comparison and benchmarking (see benchmarks/run_benchmarks.py).
"""
from __future__ import annotations


def quicksort(arr: list) -> list:
    """Average O(n log n), worst case O(n^2) (e.g. already-sorted input
    with naive pivot choice) — mitigated here with a median-of-three
    pivot selection."""
    items = list(arr)
    _quicksort(items, 0, len(items) - 1)
    return items


def _median_of_three(items, lo, hi):
    mid = (lo + hi) // 2
    trio = [(items[lo], lo), (items[mid], mid), (items[hi], hi)]
    trio.sort(key=lambda t: t[0])
    return trio[1][1]  # index of the median value


def _quicksort(items, lo, hi):
    while lo < hi:
        pivot_idx = _median_of_three(items, lo, hi)
        items[pivot_idx], items[hi] = items[hi], items[pivot_idx]
        pivot = items[hi]

        i = lo
        for j in range(lo, hi):
            if items[j] <= pivot:
                items[i], items[j] = items[j], items[i]
                i += 1
        items[i], items[hi] = items[hi], items[i]

        # recurse into the smaller partition, loop into the larger one
        # (bounds worst-case stack depth to O(log n))
        if i - lo < hi - i:
            _quicksort(items, lo, i - 1)
            lo = i + 1
        else:
            _quicksort(items, i + 1, hi)
            hi = i - 1


def mergesort(arr: list) -> list:
    """Stable O(n log n) in all cases, at the cost of O(n) extra space."""
    if len(arr) <= 1:
        return list(arr)

    mid = len(arr) // 2
    left = mergesort(arr[:mid])
    right = mergesort(arr[mid:])
    return _merge(left, right)


def _merge(left: list, right: list) -> list:
    result = []
    i = j = 0
    while i < len(left) and j < len(right):
        if left[i] <= right[j]:
            result.append(left[i])
            i += 1
        else:
            result.append(right[j])
            j += 1
    result.extend(left[i:])
    result.extend(right[j:])
    return result


def insertion_sort(arr: list) -> list:
    """O(n^2) worst case, but O(n) on nearly-sorted input — included as a
    baseline for the benchmark to make the O(n log n) wins visible."""
    items = list(arr)
    for i in range(1, len(items)):
        key = items[i]
        j = i - 1
        while j >= 0 and items[j] > key:
            items[j + 1] = items[j]
            j -= 1
        items[j + 1] = key
    return items
