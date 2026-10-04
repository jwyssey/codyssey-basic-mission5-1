"""노드 참조만으로 삽입, 삭제, 이동할 수 있는 이중 연결 리스트."""


class Node:
    """리스트의 한 칸. data에는 호출자가 원하는 객체를 저장한다."""

    def __init__(self, data=None):
        self.prev = None
        self.next = None
        self.data = data


class DoublyLinkedList:
    """양끝 더미 노드로 경계 조건을 없앤 리스트."""

    def __init__(self):
        self.head = Node()
        self.tail = Node()
        self.head.next = self.tail
        self.tail.prev = self.head
        self._size = 0

    def __len__(self):
        return self._size

    def _insert_between(self, node, left, right):
        node.prev = left
        node.next = right
        left.next = node
        right.prev = node
        self._size += 1
        return node

    def insert_front(self, data):
        """맨 앞에 넣고 나중에 O(1) 삭제할 수 있는 노드 참조를 반환한다."""
        return self._insert_between(Node(data), self.head, self.head.next)

    def insert_back(self, data):
        """맨 뒤에 넣고 노드 참조를 반환한다."""
        return self._insert_between(Node(data), self.tail.prev, self.tail)

    def remove_node(self, node):
        """이미 알고 있는 노드를 순회 없이 분리한다."""
        if node is self.head or node is self.tail or node.prev is None:
            raise ValueError("list에 속한 데이터 노드가 아닙니다")
        node.prev.next = node.next
        node.next.prev = node.prev
        node.prev = None
        node.next = None
        self._size -= 1
        return node.data

    def remove_front(self):
        """비어 있으면 None, 아니면 맨 앞 데이터를 반환한다."""
        if self._size == 0:
            return None
        return self.remove_node(self.head.next)

    def remove_back(self):
        """비어 있으면 None, 아니면 맨 뒤 데이터를 반환한다."""
        if self._size == 0:
            return None
        return self.remove_node(self.tail.prev)

    def move_to_front(self, node):
        """노드의 위치만 바꾸며 크기는 그대로 유지한다."""
        if node.prev is self.head:
            return
        self.remove_node(node)
        self._insert_between(node, self.head, self.head.next)

    def __iter__(self):
        current = self.head.next
        while current is not self.tail:
            yield current.data
            current = current.next
