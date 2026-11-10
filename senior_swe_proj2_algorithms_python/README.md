# Algorithms & Data Structures Library (Python)

Personal portfolio project: core algorithms and data structures
implemented from scratch (not via `functools.lru_cache`, `heapq`-wrapped
libraries, or `networkx`) — LRU cache, graph algorithms, and sorting
algorithms — each with a full test suite and a benchmark comparing
real runtime behavior against theoretical complexity.

## Why this project

Built to demonstrate the "solid understanding of algorithms, data
structures, and foundational computer science concepts" that backend
roles ask for directly, with working code and measured performance
rather than just a description.

## What's included

- **`lru_cache.py`** — O(1) get/put LRU cache via hash map + doubly
  linked list (the standard systems-design implementation, built from
  primitives rather than wrapping `OrderedDict`).
- **`graph.py`** — adjacency-list `Graph` class with:
  - BFS shortest path (unweighted, O(V+E))
  - Iterative DFS traversal (avoids Python recursion limits on large graphs)
  - Cycle detection (3-color DFS, correct for directed and undirected graphs)
  - Dijkstra's algorithm (binary heap, O((V+E) log V)), with explicit
    rejection of negative edge weights rather than silently returning
    wrong answers
- **`sorting.py`** — quicksort (median-of-three pivot, smaller-partition
  recursion to bound stack depth), mergesort (stable, O(n log n)
  worst-case), and insertion sort (included deliberately as an O(n²)
  baseline for the benchmark).

## Results (benchmarks/run_benchmarks.py)

At n=1000 on reverse-sorted input: insertion sort takes **44.7 ms**
while quicksort and mergesort both finish in **~1.2–1.5 ms** — a ~30x
gap that makes the O(n²) vs. O(n log n) difference concrete rather than
theoretical. Full numbers across input sizes/distributions in
`benchmarks/results.csv` (regenerated each run). Python's built-in
Timsort is, unsurprisingly, faster than all three — it's a highly
optimized hybrid algorithm with adaptive run detection; the point of
this benchmark is comparing the three from-scratch implementations
against each other and against theory, not beating the standard library.

## Run it

```bash
# tests (25 unit tests)
python -m unittest discover -s tests -v

# benchmarks
python benchmarks/run_benchmarks.py
```

No external dependencies — pure standard library.

## Project structure

```
py2_algorithms/
├── README.md
├── src/
│   ├── lru_cache.py
│   ├── graph.py
│   └── sorting.py
├── tests/
│   └── test_algorithms.py   # 25 unit tests
└── benchmarks/
    └── run_benchmarks.py    # writes results.csv on run
```
