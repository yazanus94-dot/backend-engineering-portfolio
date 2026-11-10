"""
LRU (Least Recently Used) Cache implemented from scratch using a hash map
+ doubly linked list, giving O(1) get/put — the classic interview/systems
problem, implemented as production-quality code rather than a sketch.

Does NOT use functools.lru_cache or OrderedDict's move_to_end, since the
whole point is demonstrating the underlying data-structure design.
"""
from __future__ import annotations
from typing import Any, Optional


class _Node:
    __slots__ = ("key", "value", "prev", "next")

    def __init__(self, key=None, value=None):
        self.key = key
        self.value = value
        self.prev: Optional[_Node] = None
        self.next: Optional[_Node] = None


class LRUCache:
    """Fixed-capacity cache with O(1) get and put.

    Internally: a hash map from key -> node, plus a doubly linked list
    ordered by recency (head = most recently used, tail = least recently
    used). On capacity overflow, the tail is evicted.
    """

    def __init__(self, capacity: int):
        if capacity <= 0:
            raise ValueError("capacity must be a positive integer")
        self.capacity = capacity
        self._map: dict[Any, _Node] = {}
        # sentinel head/tail nodes avoid special-casing empty-list edges
        self._head = _Node()
        self._tail = _Node()
        self._head.next = self._tail
        self._tail.prev = self._head

    def _remove(self, node: _Node) -> None:
        node.prev.next = node.next
        node.next.prev = node.prev

    def _insert_at_front(self, node: _Node) -> None:
        node.next = self._head.next
        node.prev = self._head
        self._head.next.prev = node
        self._head.next = node

    def get(self, key) -> Any:
        if key not in self._map:
            return None
        node = self._map[key]
        self._remove(node)
        self._insert_at_front(node)
        return node.value

    def put(self, key, value) -> None:
        if key in self._map:
            node = self._map[key]
            node.value = value
            self._remove(node)
            self._insert_at_front(node)
            return

        if len(self._map) >= self.capacity:
            lru_node = self._tail.prev
            self._remove(lru_node)
            del self._map[lru_node.key]

        node = _Node(key, value)
        self._map[key] = node
        self._insert_at_front(node)

    def __len__(self) -> int:
        return len(self._map)

    def __contains__(self, key) -> bool:
        return key in self._map

    def keys_in_recency_order(self) -> list:
        """Most-recently-used first. Exposed for testing/inspection."""
        result = []
        node = self._head.next
        while node is not self._tail:
            result.append(node.key)
            node = node.next
        return result
