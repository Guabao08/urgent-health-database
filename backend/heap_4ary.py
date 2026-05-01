class FourAryHeap:
    def __init__(self):
        self.heap = []

    def parent(self, i):
        return (i - 1) // 4

    def child(self, i, k):
        return 4 * i + k

    def swap(self, i, j):
        self.heap[i], self.heap[j] = self.heap[j], self.heap[i]

    def insert(self, patient):
        self.heap.append(patient)
        self._sift_up(len(self.heap) - 1)

    def extract_max(self):
        if not self.heap:
            return None
        max_patient = self.heap[0]
        last_patient = self.heap.pop()
        if self.heap:
            self.heap[0] = last_patient
            self._sift_down(0)
        return max_patient

    def _sift_up(self, i):
        while i > 0:
            p = self.parent(i)
            # Compare priority
            if self.heap[i].get("priority", 0) > self.heap[p].get("priority", 0):
                self.swap(i, p)
                i = p
            else:
                break

    def _sift_down(self, i):
        n = len(self.heap)
        while True:
            max_index = i
            max_priority = self.heap[i].get("priority", 0)

            # Check all 4 children
            for k in range(1, 5):
                c = self.child(i, k)
                if c < n:
                    child_priority = self.heap[c].get("priority", 0)
                    if child_priority > max_priority:
                        max_priority = child_priority
                        max_index = c

            if max_index != i:
                self.swap(i, max_index)
                i = max_index
            else:
                break

    def get_sorted_patients(self):
        # Return a copy sorted by priority (non-destructive)
        return sorted(self.heap, key=lambda x: x.get("priority", 0), reverse=True)

    def to_tree_format(self):
        # Convert array to a tree-like structure for the frontend visualizer
        if not self.heap:
            return None

        def build_tree(index):
            if index >= len(self.heap):
                return None
            node = self.heap[index].copy()
            node["children"] = []
            for k in range(1, 5):
                child_node = build_tree(self.child(index, k))
                if child_node:
                    node["children"].append(child_node)
            return node

        return build_tree(0)
