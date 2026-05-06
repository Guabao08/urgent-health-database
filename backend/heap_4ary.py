"""
heap_4ary.py — 4-ary Max-Heap for the VitalTriage Priority Queue

Structure
---------
A 4-ary heap is a complete tree where every node has *up to four* children.
The entire tree is stored in a single flat list (self.heap).

Index arithmetic for any node at position i:
  Parent  : (i - 1) // 4
  Child k : 4 * i + k   where k ∈ {1, 2, 3, 4}

Heap property (max-heap): every parent's priority ≥ all its children's
priorities, so self.heap[0] is always the highest-priority patient.

Why 4-ary instead of binary?
  Fewer levels → fewer sift-up comparisons when inserting (log₄ n vs log₂ n
  levels).  Sift-down is slightly more work per level (compare 4 children
  instead of 2), but cache-friendly access patterns keep it fast in practice.
"""
from __future__ import annotations

from typing import Dict, List, Optional, Any


class FourAryHeap:
    """
    Max-heap where each node may have up to four children.

    Each element is a patient dict that must contain at least:
        "priority" (int, 1–20)  — higher value = more urgent

    Public API
    ----------
    insert(patient)          O(log₄ n)  — add a patient and restore heap order
    extract_max()            O(log₄ n)  — remove & return the most urgent patient
    peek()                   O(1)       — return max without removing it
    get_sorted_patients()    O(n log n) — sorted copy, heap unchanged
    build_from_list(items)   O(n)       — bulk-load via Floyd's algorithm
    to_tree_format()                    — nested dict tree for JSON/frontend
    depth_levels()                      — list of lists, one per depth level
    size                     property   — current patient count
    is_empty                 property   — True when queue is empty
    """

    def __init__(self) -> None:
        self.heap: List[Dict[str, Any]] = []

    # ── Index helpers ─────────────────────────────────────────────────────────

    def _parent(self, i: int) -> int:
        """Index of the parent of node i."""
        return (i - 1) // 4

    def _child(self, i: int, k: int) -> int:
        """Index of the k-th child (k = 1…4) of node i."""
        return 4 * i + k

    def _swap(self, i: int, j: int) -> None:
        self.heap[i], self.heap[j] = self.heap[j], self.heap[i]

    def _priority(self, i: int) -> int:
        return self.heap[i].get("priority", 0)

    # ── Core heap operations ──────────────────────────────────────────────────

    def insert(self, patient: Dict[str, Any]) -> None:
        """
        Append patient at the end of the array, then sift it upward until the
        heap property is restored.  O(log₄ n) comparisons.
        """
        self.heap.append(patient)
        self._sift_up(len(self.heap) - 1)

    def extract_max(self) -> Optional[Dict[str, Any]]:
        """
        Swap root with the last element, pop it off, then sift the new root
        down to its correct position.  Returns the highest-priority patient,
        or None if the heap is empty.  O(log₄ n) comparisons.
        """
        if not self.heap:
            return None
        max_patient = self.heap[0]
        last = self.heap.pop()
        if self.heap:
            self.heap[0] = last
            self._sift_down(0)
        return max_patient

    def peek(self) -> Optional[Dict[str, Any]]:
        """Return the highest-priority patient without removing it.  O(1)."""
        return self.heap[0] if self.heap else None

    # ── Sift helpers ──────────────────────────────────────────────────────────

    def _sift_up(self, i: int) -> None:
        """
        Bubble node i upward: while it has higher priority than its parent,
        swap with the parent and move up one level.
        """
        while i > 0:
            p = self._parent(i)
            if self._priority(i) > self._priority(p):
                self._swap(i, p)
                i = p
            else:
                break

    def _sift_down(self, i: int) -> None:
        """
        Push node i downward: find the largest child; if it outranks the node,
        swap and continue down that branch.  Repeat until in-place.
        """
        n = len(self.heap)
        while True:
            largest = i
            largest_priority = self._priority(i)

            for k in range(1, 5):           # check all 4 potential children
                c = self._child(i, k)
                if c < n and self._priority(c) > largest_priority:
                    largest_priority = self._priority(c)
                    largest = c

            if largest != i:
                self._swap(i, largest)
                i = largest
            else:
                break                       # heap property satisfied

    # ── Bulk build ────────────────────────────────────────────────────────────

    @classmethod
    def build_from_list(cls, patients: List[Dict[str, Any]]) -> "FourAryHeap":
        """
        Construct a valid heap from an unordered list in O(n) time using
        Floyd's heap-construction algorithm: load all items directly into the
        array, then sift down every non-leaf node from bottom to top.
        """
        h = cls()
        h.heap = list(patients)
        for i in range((len(h.heap) - 2) // 4, -1, -1):
            h._sift_down(i)
        return h

    # ── Queries ───────────────────────────────────────────────────────────────

    def get_sorted_patients(self) -> List[Dict[str, Any]]:
        """
        Return all patients sorted by descending priority without modifying
        the heap.  Creates a shallow copy and sorts it — O(n log n).
        """
        return sorted(self.heap, key=lambda p: p.get("priority", 0), reverse=True)

    # ── Visualisation helpers ─────────────────────────────────────────────────

    def to_tree_format(self) -> Optional[Dict[str, Any]]:
        """
        Convert the flat heap array into a nested dict tree suitable for JSON
        serialisation and tree-rendering on the frontend.

        Each node dict mirrors the patient data and adds a "children" list
        containing up to four nested child dicts.
        """
        if not self.heap:
            return None

        def _build(index: int) -> Optional[Dict[str, Any]]:
            if index >= len(self.heap):
                return None
            node = self.heap[index].copy()
            node["children"] = [
                child
                for k in range(1, 5)
                for child in [_build(self._child(index, k))]
                if child is not None
            ]
            return node

        return _build(0)

    def depth_levels(self) -> List[List[Dict[str, Any]]]:
        """
        Return the heap partitioned into depth levels (level 0 = root).
        Useful for level-by-level display or debugging.
        """
        if not self.heap:
            return []
        levels: List[List[Dict[str, Any]]] = []
        level_start = 0
        level_size = 1
        while level_start < len(self.heap):
            levels.append(self.heap[level_start : level_start + level_size])
            level_start += level_size
            level_size *= 4
        return levels

    # ── Properties ────────────────────────────────────────────────────────────

    @property
    def size(self) -> int:
        return len(self.heap)

    @property
    def is_empty(self) -> bool:
        return len(self.heap) == 0

    # ── Dunder helpers ────────────────────────────────────────────────────────

    def __len__(self) -> int:
        return len(self.heap)

    def __repr__(self) -> str:
        top = self.heap[0].get("priority") if self.heap else "—"
        return f"FourAryHeap(size={len(self.heap)}, max_priority={top})"
