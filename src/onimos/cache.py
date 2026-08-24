from __future__ import annotations
import threading
import time
from collections import OrderedDict


class TTLCache:
    """
    Cache de baixa latência na frente do repositório -- o online store da
    analogia com feature store. Só serve consulta "agora" (as_of=None);
    consulta ponto-no-tempo pra auditoria vai direto no repositório, porque
    é rara e precisa do dado exato daquele momento, não compensa cachear.
    """

    def __init__(self, ttl_seconds: float = 30.0, max_size: int = 50_000):
        self._ttl = ttl_seconds
        self._max_size = max_size
        self._data: OrderedDict[str, tuple[float, object]] = OrderedDict()
        self._lock = threading.Lock()
        self.hits = 0
        self.misses = 0

    def get(self, key: str):
        with self._lock:
            item = self._data.get(key)
            if item is None:
                self.misses += 1
                return None
            expires_at, value = item
            if time.monotonic() > expires_at:
                del self._data[key]
                self.misses += 1
                return None
            self._data.move_to_end(key)
            self.hits += 1
            return value

    def set(self, key: str, value) -> None:
        with self._lock:
            self._data[key] = (time.monotonic() + self._ttl, value)
            self._data.move_to_end(key)
            while len(self._data) > self._max_size:
                self._data.popitem(last=False)

    def invalidate_all(self) -> None:
        with self._lock:
            self._data.clear()
