import sys
import os
import random
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from lru_cache import LRUCache  # noqa: E402
from graph import Graph, bfs_shortest_path, dfs_traversal, has_cycle, dijkstra  # noqa: E402
from sorting import quicksort, mergesort, insertion_sort  # noqa: E402


class LRUCacheTest(unittest.TestCase):
    def test_invalid_capacity_rejected(self):
        with self.assertRaises(ValueError):
            LRUCache(0)
        with self.assertRaises(ValueError):
            LRUCache(-5)

    def test_basic_get_put(self):
        cache = LRUCache(2)
        cache.put("a", 1)
        cache.put("b", 2)
        self.assertEqual(cache.get("a"), 1)
        self.assertEqual(cache.get("b"), 2)
        self.assertIsNone(cache.get("missing"))

    def test_eviction_order(self):
        cache = LRUCache(2)
        cache.put("a", 1)
        cache.put("b", 2)
        cache.put("c", 3)  # should evict "a" (least recently used)
        self.assertIsNone(cache.get("a"))
        self.assertEqual(cache.get("b"), 2)
        self.assertEqual(cache.get("c"), 3)

    def test_get_refreshes_recency(self):
        cache = LRUCache(2)
        cache.put("a", 1)
        cache.put("b", 2)
        cache.get("a")        # "a" is now most recently used
        cache.put("c", 3)     # should evict "b", not "a"
        self.assertEqual(cache.get("a"), 1)
        self.assertIsNone(cache.get("b"))

    def test_update_existing_key_refreshes_recency(self):
        cache = LRUCache(2)
        cache.put("a", 1)
        cache.put("b", 2)
        cache.put("a", 100)   # update, should also refresh recency
        cache.put("c", 3)     # should evict "b"
        self.assertEqual(cache.get("a"), 100)
        self.assertIsNone(cache.get("b"))

    def test_len_and_contains(self):
        cache = LRUCache(3)
        cache.put("x", 1)
        self.assertEqual(len(cache), 1)
        self.assertIn("x", cache)
        self.assertNotIn("y", cache)


class GraphBFSTest(unittest.TestCase):
    def setUp(self):
        self.g = Graph(directed=False)
        for u, v in [("A", "B"), ("B", "C"), ("C", "D"), ("A", "E"), ("E", "D")]:
            self.g.add_edge(u, v)

    def test_shortest_path_found(self):
        path = bfs_shortest_path(self.g, "A", "D")
        self.assertEqual(path[0], "A")
        self.assertEqual(path[-1], "D")
        self.assertEqual(len(path), 3)  # A-E-D or A-B-C-D's shorter alt (A-E-D len 3)

    def test_same_start_and_goal(self):
        self.assertEqual(bfs_shortest_path(self.g, "A", "A"), ["A"])

    def test_unreachable_node(self):
        self.g.add_node("isolated")
        self.assertIsNone(bfs_shortest_path(self.g, "A", "isolated"))

    def test_nonexistent_node(self):
        self.assertIsNone(bfs_shortest_path(self.g, "A", "does_not_exist"))


class GraphDFSAndCycleTest(unittest.TestCase):
    def test_dfs_visits_all_reachable_nodes(self):
        g = Graph(directed=False)
        g.add_edge("A", "B")
        g.add_edge("B", "C")
        order = dfs_traversal(g, "A")
        self.assertEqual(set(order), {"A", "B", "C"})
        self.assertEqual(order[0], "A")

    def test_dfs_empty_for_unknown_start(self):
        g = Graph()
        self.assertEqual(dfs_traversal(g, "nope"), [])

    def test_cycle_detected_undirected(self):
        g = Graph(directed=False)
        g.add_edge("A", "B")
        g.add_edge("B", "C")
        g.add_edge("C", "A")
        self.assertTrue(has_cycle(g))

    def test_no_cycle_in_tree(self):
        g = Graph(directed=False)
        g.add_edge("A", "B")
        g.add_edge("A", "C")
        g.add_edge("B", "D")
        self.assertFalse(has_cycle(g))

    def test_cycle_detected_directed(self):
        g = Graph(directed=True)
        g.add_edge("A", "B")
        g.add_edge("B", "C")
        g.add_edge("C", "A")
        self.assertTrue(has_cycle(g))

    def test_no_cycle_directed_dag(self):
        g = Graph(directed=True)
        g.add_edge("A", "B")
        g.add_edge("A", "C")
        g.add_edge("B", "C")
        self.assertFalse(has_cycle(g))


class DijkstraTest(unittest.TestCase):
    def test_shortest_distances(self):
        g = Graph(directed=True)
        g.add_edge("A", "B", 4)
        g.add_edge("A", "C", 1)
        g.add_edge("C", "B", 1)
        g.add_edge("B", "D", 1)
        distances = dijkstra(g, "A")
        self.assertEqual(distances["A"], 0)
        self.assertEqual(distances["B"], 2)  # A->C->B (1+1) beats A->B (4)
        self.assertEqual(distances["C"], 1)
        self.assertEqual(distances["D"], 3)

    def test_unreachable_node_has_infinite_distance(self):
        g = Graph(directed=True)
        g.add_edge("A", "B", 1)
        g.add_node("isolated")
        distances = dijkstra(g, "A")
        self.assertEqual(distances["isolated"], float("inf"))

    def test_negative_weight_rejected(self):
        g = Graph(directed=True)
        g.add_edge("A", "B", -1)
        with self.assertRaises(ValueError):
            dijkstra(g, "A")


class SortingTest(unittest.TestCase):
    def test_sorts_match_builtin_sorted_on_random_data(self):
        rng = random.Random(42)
        data = [rng.randint(-1000, 1000) for _ in range(500)]
        expected = sorted(data)
        self.assertEqual(quicksort(data), expected)
        self.assertEqual(mergesort(data), expected)
        self.assertEqual(insertion_sort(data), expected)

    def test_empty_and_single_element(self):
        for fn in (quicksort, mergesort, insertion_sort):
            self.assertEqual(fn([]), [])
            self.assertEqual(fn([5]), [5])

    def test_already_sorted_input(self):
        data = list(range(100))
        for fn in (quicksort, mergesort, insertion_sort):
            self.assertEqual(fn(data), data)

    def test_reverse_sorted_input(self):
        data = list(range(100, 0, -1))
        expected = sorted(data)
        for fn in (quicksort, mergesort, insertion_sort):
            self.assertEqual(fn(data), expected)

    def test_duplicates(self):
        data = [5, 3, 5, 1, 3, 5, 2, 1]
        expected = sorted(data)
        for fn in (quicksort, mergesort, insertion_sort):
            self.assertEqual(fn(data), expected)

    def test_original_input_not_mutated(self):
        data = [3, 1, 2]
        original_copy = list(data)
        quicksort(data)
        mergesort(data)
        insertion_sort(data)
        self.assertEqual(data, original_copy)


if __name__ == "__main__":
    unittest.main()
