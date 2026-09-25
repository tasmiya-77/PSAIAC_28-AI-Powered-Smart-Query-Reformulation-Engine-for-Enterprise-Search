import time
import hashlib
import json
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class SearchCacheService:
    def __init__(self, max_items: int = 200, default_ttl_seconds: int = 300):
        self.max_items = max_items
        self.default_ttl = default_ttl_seconds
        self._cache: Dict[str, Dict[str, Any]] = {}

    def _generate_key(self, query: str, filters: Dict[str, Any], mode: str) -> str:
        raw_str = f"{query.strip().lower()}:{mode}:{json.dumps(filters, sort_keys=True)}"
        return hashlib.sha256(raw_str.encode("utf-8")).hexdigest()

    def get(self, query: str, filters: Dict[str, Any], mode: str) -> Optional[Dict[str, Any]]:
        key = self._generate_key(query, filters, mode)
        entry = self._cache.get(key)
        if not entry:
            return None

        # Check TTL
        if time.time() - entry["timestamp"] > self.default_ttl:
            del self._cache[key]
            return None

        logger.info(f"Search cache HIT for query: '{query}'")
        return entry["data"]

    def set(self, query: str, filters: Dict[str, Any], mode: str, data: Dict[str, Any]):
        key = self._generate_key(query, filters, mode)
        
        # Evict oldest if full
        if len(self._cache) >= self.max_items:
            oldest_key = min(self._cache.keys(), key=lambda k: self._cache[k]["timestamp"])
            del self._cache[oldest_key]

        self._cache[key] = {
            "timestamp": time.time(),
            "data": data,
        }
        logger.info(f"Search cache STORED for query: '{query}'")

    def clear(self):
        self._cache.clear()


search_cache = SearchCacheService()
