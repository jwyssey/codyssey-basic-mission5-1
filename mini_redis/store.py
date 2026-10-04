"""문자열 저장, LRU 순서, TTL 및 메모리 제한을 함께 관리한다."""

import math
import time

from .doubly_linked_list import DoublyLinkedList
from .hashmap import HashMap
from .heap import MinHeap


def _byte_size(text):
    return len(text.encode("utf-8"))


class _Entry:
    """해시맵 값과 LRU/TTL 노드 참조를 하나로 묶는다."""

    def __init__(self, key, value):
        self.key = key
        self.value = value
        self.lru_node = None
        self.expire_at = None
        self.ttl_node = None

    @property
    def byte_size(self):
        return _byte_size(self.key) + _byte_size(self.value)


class MiniRedis:
    """단일 프로세스에서 사용되는 인메모리 저장소."""

    def __init__(self, clock=None):
        self._clock = clock if clock is not None else time.monotonic
        self._data = HashMap()
        self._lru = DoublyLinkedList()  # 앞: 최근 사용, 뒤: 가장 오래된 사용
        self._expirations = MinHeap()
        self.used_memory = 0
        self.maxmemory = 0
        self.evicted_keys = 0

    def _delete(self, entry):
        """한 키의 데이터, LRU, TTL, 메모리 사용량을 같이 정리한다."""
        self._data.remove(entry.key)
        self._lru.remove_node(entry.lru_node)
        if entry.ttl_node is not None:
            self._expirations.remove(entry.ttl_node)
            entry.ttl_node = None
            entry.expire_at = None
        self.used_memory -= entry.byte_size

    def _purge_expired(self):
        """힙 맨 위부터 지금까지 만료된 키를 모두 제거한다."""
        now = self._clock()
        while self._expirations.size() and self._expirations.peek()[0] <= now:
            _, key = self._expirations.peek()
            self._delete(self._data.get(key))

    def _evict_until_fits(self):
        while self.maxmemory and self.used_memory > self.maxmemory:
            oldest = self._lru.tail.prev.data
            self._delete(oldest)
            self.evicted_keys += 1

    def set(self, key, value):
        """단일 엔트리가 너무 크면 기존 데이터도 바꾸지 않고 OOM을 반환한다."""
        self._purge_expired()
        new_size = _byte_size(key) + _byte_size(value)
        if self.maxmemory and new_size > self.maxmemory:
            return False

        entry = self._data.get(key)
        if entry is None:
            entry = _Entry(key, value)
            entry.lru_node = self._lru.insert_front(entry)
            self._data.put(key, entry)
            self.used_memory += new_size
        else:
            self.used_memory += new_size - entry.byte_size
            entry.value = value
            if entry.ttl_node is not None:
                self._expirations.remove(entry.ttl_node)
                entry.ttl_node = None
                entry.expire_at = None
            self._lru.move_to_front(entry.lru_node)
        self._evict_until_fits()
        return True

    def get(self, key):
        self._purge_expired()
        entry = self._data.get(key)
        if entry is None:
            return None
        self._lru.move_to_front(entry.lru_node)
        return entry.value

    def delete(self, key):
        self._purge_expired()
        entry = self._data.get(key)
        if entry is None:
            return 0
        self._delete(entry)
        return 1

    def exists(self, key):
        self._purge_expired()
        return int(self._data.contains(key))

    def dbsize(self):
        self._purge_expired()
        return self._data.size()

    def keys(self):
        self._purge_expired()
        return self._data.keys()

    def config_set_maxmemory(self, limit):
        self._purge_expired()
        self.maxmemory = limit
        self._evict_until_fits()

    def info_memory(self):
        self._purge_expired()
        return (
            "used_memory:{}\nmaxmemory:{}\nevicted_keys:{}".format(
                self.used_memory, self.maxmemory, self.evicted_keys
            )
        )

    def expire(self, key, seconds):
        self._purge_expired()
        entry = self._data.get(key)
        if entry is None:
            return 0
        if seconds <= 0:
            self._delete(entry)
            return 1
        if entry.ttl_node is not None:
            self._expirations.remove(entry.ttl_node)
        entry.expire_at = self._clock() + seconds
        entry.ttl_node = self._expirations.push((entry.expire_at, key))
        return 1

    def ttl(self, key):
        self._purge_expired()
        entry = self._data.get(key)
        if entry is None:
            return -2
        if entry.expire_at is None:
            return -1
        return max(0, math.ceil(entry.expire_at - self._clock()))
