"""UTF-8 해시와 체이닝을 직접 구현한 문자열 키 해시맵."""

from .doubly_linked_list import DoublyLinkedList


class _Pair:
    def __init__(self, key, value):
        self.key = key
        self.value = value


class HashMap:
    """로드 팩터가 0.75를 넘으면 버킷을 두 배로 늘린다."""

    def __init__(self, capacity=8):
        if capacity < 1:
            raise ValueError("capacity는 1 이상이어야 합니다")
        self._buckets = [DoublyLinkedList() for _ in range(capacity)]
        self._size = 0

    @staticmethod
    def _hash(key):
        """문자열의 바이트 순서를 반영하는 결정적 다항식 해시."""
        result = 0
        for byte in key.encode("utf-8"):
            result = (result * 31 + byte) & 0xFFFFFFFFFFFFFFFF
        return result

    def _bucket(self, key):
        return self._buckets[self._hash(key) % len(self._buckets)]

    def _find(self, key):
        for pair in self._bucket(key):
            if pair.key == key:
                return pair
        return None

    def put(self, key, value):
        """키를 추가하거나 값을 덮어쓰고, 기존 값이 있으면 반환한다."""
        pair = self._find(key)
        if pair is not None:
            old_value = pair.value
            pair.value = value
            return old_value
        self._bucket(key).insert_back(_Pair(key, value))
        self._size += 1
        if self._size * 4 > len(self._buckets) * 3:
            self._resize()
        return None

    def get(self, key):
        pair = self._find(key)
        return None if pair is None else pair.value

    def remove(self, key):
        bucket = self._bucket(key)
        node = bucket.head.next
        while node is not bucket.tail:
            if node.data.key == key:
                value = node.data.value
                bucket.remove_node(node)
                self._size -= 1
                return value
            node = node.next
        return None

    def contains(self, key):
        return self._find(key) is not None

    def keys(self):
        result = []
        for bucket in self._buckets:
            for pair in bucket:
                result.append(pair.key)
        return result

    def size(self):
        return self._size

    def _resize(self):
        """버킷 수가 바뀌므로 모든 키의 인덱스를 다시 계산한다."""
        old_buckets = self._buckets
        self._buckets = [DoublyLinkedList() for _ in range(len(old_buckets) * 2)]
        for bucket in old_buckets:
            for pair in bucket:
                self._bucket(pair.key).insert_back(pair)
