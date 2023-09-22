import numpy as np


class dynamic_cache:
    def __init__(self,size):
        self.size = size
    
    def add(self):
        pass
    def prefetch(self):
        pass


class LRU_cache:
    def __init__(self, capacity,offsetSize=100): # offsetSize知る必要ある？
        self.capacity = capacity
        self.SizeOfFloat = 4
        self.BlockX = offsetSize
        self.BlockY = offsetSize
        self.BlockZ = offsetSize
        self.blocksize = self.SizeOfFloat*self.BlockX*self.BlockY*self.BlockZ
        self.cache = {}  # Dictionary to store cached items
        self.order = []  # List to maintain the order of items


    # key = (tol,timestep,x,y,z) x,y,zはブロックのサイズで割れる値です。
    def get(self, key):
        if key in self.cache:
            # Move the accessed item to the end (most recently used)
            self.order.remove(key)
            self.order.append(key)
            return self.cache[key]
        return None

    def put(self, key, value):
        if key in self.cache:
            # Update the value and move the item to the end
            self.order.remove(key)
        elif len(self.cache) >= self.capacity:
            # Evict the least recently used item
            oldest_key = self.order.pop(0)
            self.cache.pop(oldest_key)
        self.cache[key] = value
        self.order.append(key)

# Example usage

if __name__ == "__main__":
    cache_capacity = 3
    lru_cache = LRU_cache(cache_capacity)

    lru_cache.put("key1", "value1")
    lru_cache.put("key2", "value2")
    lru_cache.put("key3", "value3")

    print(lru_cache.get("key2"))  # Output: "value2"

    print()
    lru_cache.put("key4", "value4")  # This will evict "key1" as it's the least recently used

    print(lru_cache.get("key1"))  # Output: None, as "key1" was evicted

    if lru_cache.get("key5") == None:
        print("go get to next level cache")
    else:
        print("hit!")
