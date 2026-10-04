"""자료구조 불변식과 명세의 주요 상태 전이를 검증한다."""

import unittest

from mini_redis.doubly_linked_list import DoublyLinkedList
from mini_redis.hashmap import HashMap
from mini_redis.heap import MinHeap
from mini_redis.main import execute
from mini_redis.store import MiniRedis


class StructureTests(unittest.TestCase):
    def test_list_moves_and_removes_known_node(self):
        items = DoublyLinkedList()
        first = items.insert_back("first")
        items.insert_back("second")
        items.move_to_front(first)
        self.assertEqual(list(items), ["first", "second"])
        self.assertEqual(items.remove_node(first), "first")
        self.assertEqual(items.remove_back(), "second")
        self.assertIsNone(items.remove_front())

    def test_hash_collisions_and_resize(self):
        mapping = HashMap(capacity=1)
        for index in range(30):
            mapping.put("key:{}".format(index), index)
        self.assertEqual(mapping.size(), 30)
        self.assertEqual(len(mapping.keys()), 30)
        for index in range(30):
            self.assertEqual(mapping.get("key:{}".format(index)), index)
        self.assertEqual(mapping.remove("key:4"), 4)
        self.assertFalse(mapping.contains("key:4"))

    def test_heap_removes_middle_item(self):
        heap = MinHeap()
        heap.push((5, "five"))
        middle = heap.push((3, "three"))
        heap.push((1, "one"))
        self.assertEqual(heap.remove(middle), (3, "three"))
        self.assertEqual(heap.pop(), (1, "one"))
        self.assertEqual(heap.pop(), (5, "five"))
        self.assertIsNone(heap.pop())


class StoreTests(unittest.TestCase):
    def setUp(self):
        self.now = 100.0
        self.store = MiniRedis(clock=lambda: self.now)

    def test_lru_memory_and_utf8_bytes(self):
        self.store.config_set_maxmemory(9)
        self.assertTrue(self.store.set("가", "나"))  # 3 + 3 bytes
        self.assertTrue(self.store.set("a", "1"))   # 1 + 1 bytes
        self.assertEqual(self.store.get("가"), "나")
        self.assertTrue(self.store.set("b", "2"))
        self.assertEqual(self.store.get("a"), None)
        self.assertEqual(self.store.used_memory, 8)
        self.assertEqual(self.store.evicted_keys, 1)

    def test_expiration_overwrite_delete_and_oom_are_consistent(self):
        self.store.set("key", "old")
        self.store.expire("key", 10)
        self.assertEqual(self.store.ttl("key"), 10)
        self.store.config_set_maxmemory(7)
        self.assertFalse(self.store.set("key", "oversized"))
        self.assertEqual(self.store.get("key"), "old")
        self.assertEqual(self.store.ttl("key"), 10)
        self.assertTrue(self.store.set("key", "new"))
        self.assertEqual(self.store.ttl("key"), -1)
        self.assertEqual(self.store._expirations.size(), 0)
        self.store.expire("key", 2)
        self.now += 2
        self.assertIsNone(self.store.get("key"))
        self.assertEqual(self.store.dbsize(), 0)
        self.assertEqual(self.store.used_memory, 0)
        self.assertEqual(self.store._expirations.size(), 0)

    def test_config_lower_limit_evicts_immediately(self):
        self.store.set("a", "1")
        self.store.set("b", "2")
        self.store.config_set_maxmemory(2)
        self.assertEqual(self.store.keys(), ["b"])
        self.assertEqual(self.store.evicted_keys, 1)

    def test_delete_cancels_expiration_and_missing_key_rules(self):
        self.assertEqual(self.store.expire("missing", 5), 0)
        self.assertEqual(self.store.ttl("missing"), -2)
        self.store.set("a", "1")
        self.assertEqual(self.store.ttl("a"), -1)
        self.store.expire("a", 10)
        self.assertEqual(self.store._expirations.size(), 1)
        self.assertEqual(self.store.delete("a"), 1)
        self.assertEqual(self.store._expirations.size(), 0)
        self.assertEqual(self.store.used_memory, 0)
        self.assertEqual(self.store.delete("a"), 0)

    def test_cli_errors_and_quotes(self):
        self.assertEqual(execute(self.store, 'SET name "Alice Kim"'), "OK")
        self.assertEqual(execute(self.store, "GET name"), '"Alice Kim"')
        self.assertEqual(execute(self.store, "SET surname O'Reilly"), "OK")
        self.assertEqual(execute(self.store, "GET surname"), '"O\'Reilly"')
        self.assertEqual(execute(self.store, "GET"),
                         "(error) ERR wrong number of arguments for 'GET' command")
        self.assertEqual(execute(self.store, "EXPIRE name x"),
                         "(error) ERR value is not an integer or out of range")
        self.assertEqual(execute(self.store, "FOO"),
                         "(error) ERR unknown command 'FOO'")


if __name__ == "__main__":
    unittest.main()
