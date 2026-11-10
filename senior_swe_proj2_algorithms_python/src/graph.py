"""
Graph algorithms implemented from scratch on a simple adjacency-list
Graph class: BFS (shortest path by edge count), DFS (traversal +
cycle detection), and Dijkstra's algorithm (shortest path by weight,
using a binary heap for O((V+E) log V) performance).
"""
from __future__ import annotations
import heapq
from collections import deque
from typing import Hashable, Optional


class Graph:
    def __init__(self, directed: bool = False):
        self.directed = directed
        self._adj: dict[Hashable, dict[Hashable, float]] = {}

    def add_node(self, node: Hashable) -> None:
        self._adj.setdefault(node, {})

    def add_edge(self, u: Hashable, v: Hashable, weight: float = 1.0) -> None:
        self.add_node(u)
        self.add_node(v)
        self._adj[u][v] = weight
        if not self.directed:
            self._adj[v][u] = weight

    def neighbors(self, node: Hashable):
        return self._adj.get(node, {})

    @property
    def nodes(self):
        return list(self._adj.keys())


def bfs_shortest_path(graph: Graph, start: Hashable, goal: Hashable) -> Optional[list]:
    """Shortest path by number of edges (unweighted). O(V + E)."""
    if start not in graph._adj or goal not in graph._adj:
        return None
    if start == goal:
        return [start]

    visited = {start}
    parent: dict[Hashable, Hashable] = {}
    queue = deque([start])

    while queue:
        current = queue.popleft()
        for neighbor in graph.neighbors(current):
            if neighbor in visited:
                continue
            visited.add(neighbor)
            parent[neighbor] = current
            if neighbor == goal:
                path = [goal]
                while path[-1] != start:
                    path.append(parent[path[-1]])
                return list(reversed(path))
            queue.append(neighbor)

    return None  # goal unreachable


def dfs_traversal(graph: Graph, start: Hashable) -> list:
    """Iterative DFS traversal order (avoids recursion-depth limits on
    large graphs, unlike a naive recursive implementation)."""
    if start not in graph._adj:
        return []

    visited = set()
    order = []
    stack = [start]

    while stack:
        node = stack.pop()
        if node in visited:
            continue
        visited.add(node)
        order.append(node)
        # push in reverse so traversal visits neighbors in insertion order
        for neighbor in reversed(list(graph.neighbors(node))):
            if neighbor not in visited:
                stack.append(neighbor)

    return order


def has_cycle(graph: Graph) -> bool:
    """Cycle detection via DFS with a recursion-free 3-color scheme
    (white/gray/black), correct for both directed and undirected graphs."""
    WHITE, GRAY, BLACK = 0, 1, 2
    color = {node: WHITE for node in graph.nodes}

    def visit(node, parent):
        color[node] = GRAY
        for neighbor in graph.neighbors(node):
            if not graph.directed and neighbor == parent:
                continue  # don't treat the edge back to parent as a cycle
            if color[neighbor] == GRAY:
                return True
            if color[neighbor] == WHITE and visit(neighbor, node):
                return True
        color[node] = BLACK
        return False

    for node in graph.nodes:
        if color[node] == WHITE:
            if visit(node, None):
                return True
    return False


def dijkstra(graph: Graph, start: Hashable) -> dict[Hashable, float]:
    """Shortest path distances from start to every reachable node, using
    a binary heap. O((V + E) log V). Raises ValueError on a negative edge
    weight, since Dijkstra's algorithm is not correct in that case."""
    for u in graph.nodes:
        for v, w in graph.neighbors(u).items():
            if w < 0:
                raise ValueError(f"negative edge weight ({u}->{v}: {w}) is not supported by Dijkstra's algorithm")

    distances = {node: float("inf") for node in graph.nodes}
    distances[start] = 0
    visited = set()
    heap = [(0, start)]

    while heap:
        dist, node = heapq.heappop(heap)
        if node in visited:
            continue
        visited.add(node)

        for neighbor, weight in graph.neighbors(node).items():
            new_dist = dist + weight
            if new_dist < distances[neighbor]:
                distances[neighbor] = new_dist
                heapq.heappush(heap, (new_dist, neighbor))

    return distances
