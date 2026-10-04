"""TTL 작업을 임의로 취소할 수도 있는 배열 기반 최소 힙."""


class HeapNode:
    """힙 원소의 현재 위치를 기억해 O(log n) 제거를 가능하게 한다."""

    def __init__(self, value, index):
        self.value = value
        self.index = index


class MinHeap:
    """튜플처럼 비교 가능한 값을 저장하는 최소 힙."""

    def __init__(self):
        self._items = []

    def size(self):
        return len(self._items)

    def peek(self):
        return None if not self._items else self._items[0].value

    def push(self, value):
        """원소를 넣고 취소 시 사용할 핸들을 반환한다."""
        node = HeapNode(value, len(self._items))
        self._items.append(node)
        self._heapify_up(node.index)
        return node

    def pop(self):
        if not self._items:
            return None
        return self.remove(self._items[0])

    def remove(self, node):
        """핸들로 지정한 원소를 제거한다. DEL과 TTL 재설정에 사용한다."""
        index = node.index
        if index < 0 or index >= len(self._items) or self._items[index] is not node:
            raise ValueError("힙에 없는 원소입니다")
        last = self._items.pop()
        node.index = -1
        if index < len(self._items):
            self._items[index] = last
            last.index = index
            parent = (index - 1) // 2
            if index > 0 and self._items[index].value < self._items[parent].value:
                self._heapify_up(index)
            else:
                self._heapify_down(index)
        return node.value

    def _swap(self, left, right):
        self._items[left], self._items[right] = self._items[right], self._items[left]
        self._items[left].index = left
        self._items[right].index = right

    def _heapify_up(self, index):
        while index > 0:
            parent = (index - 1) // 2
            if self._items[parent].value <= self._items[index].value:
                return
            self._swap(parent, index)
            index = parent

    def _heapify_down(self, index):
        length = len(self._items)
        while True:
            left = index * 2 + 1
            right = left + 1
            smallest = index
            if left < length and self._items[left].value < self._items[smallest].value:
                smallest = left
            if right < length and self._items[right].value < self._items[smallest].value:
                smallest = right
            if smallest == index:
                return
            self._swap(index, smallest)
            index = smallest
