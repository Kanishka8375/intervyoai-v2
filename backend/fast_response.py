"""
Fast Response Optimization Module
Target: <50ms response time for real-time transcription
"""

import asyncio
import time
import logging
from typing import Optional, Dict, Any
from dataclasses import dataclass
from functools import lru_cache
import hashlib

logger = logging.getLogger(__name__)


@dataclass
class FastResponseConfig:
    """Fast response configuration"""

    enable_caching: bool = True
    cache_ttl: int = 300  # 5 minutes
    enable_prefetch: bool = True
    max_cache_size: int = 1000
    stream_threshold: int = 100  # chars


class FastResponseManager:
    """
    Manages fast responses with caching and optimization
    Target: <50ms response time
    """

    def __init__(self):
        self.config = FastResponseConfig()
        self._cache: Dict[str, tuple] = {}  # key -> (result, timestamp)
        self._hit_count = 0
        self._miss_count = 0

    def _get_cache_key(self, prompt: str, role: str, provider: str) -> str:
        """Generate cache key from prompt"""
        key_str = f"{prompt}:{role}:{provider}"
        return hashlib.md5(key_str.encode()).hexdigest()

    def get_cached(self, prompt: str, role: str, provider: str) -> Optional[str]:
        """Get cached response"""
        if not self.config.enable_caching:
            return None

        key = self._get_cache_key(prompt, role, provider)
        if key in self._cache:
            result, timestamp = self._cache[key]
            # Check TTL
            if time.time() - timestamp < self.config.cache_ttl:
                self._hit_count += 1
                logger.debug(
                    f"Cache hit ({self._hit_count} hits, {self._miss_count} misses)"
                )
                return result
            else:
                # Expired
                del self._cache[key]

        self._miss_count += 1
        return None

    def set_cached(self, prompt: str, role: str, provider: str, result: str):
        """Cache response"""
        if not self.config.enable_caching:
            return

        # Evict old entries if cache is full
        if len(self._cache) >= self.config.max_cache_size:
            # Remove oldest 10%
            sorted_cache = sorted(self._cache.items(), key=lambda x: x[1][1])
            for key, _ in sorted_cache[: self.config.max_cache_size // 10]:
                del self._cache[key]

        key = self._get_cache_key(prompt, role, provider)
        self._cache[key] = (result, time.time())

    def clear_cache(self):
        """Clear all cached responses"""
        self._cache.clear()
        logger.info("Response cache cleared")

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        total = self._hit_count + self._miss_count
        hit_rate = (self._hit_count / total * 100) if total > 0 else 0
        return {
            "hits": self._hit_count,
            "misses": self._miss_count,
            "hit_rate": f"{hit_rate:.1f}%",
            "cache_size": len(self._cache),
        }

    async def fast_generate(
        self, generate_func, prompt: str, role: str, provider: str, **kwargs
    ) -> str:
        """Generate response with fast path optimization"""
        start_time = time.time()

        # Check cache first
        cached = self.get_cached(prompt, role, provider)
        if cached:
            logger.debug(
                f"Cache hit, returning in {time.time() - start_time * 1000:.1f}ms"
            )
            return cached

        # Generate response
        result = await generate_func(prompt, **kwargs)

        # Cache result
        self.set_cached(prompt, role, provider, result)

        elapsed = time.time() - start_time
        logger.debug(f"Generation completed in {elapsed * 1000:.1f}ms")

        return result


# Global instance
fast_response = FastResponseManager()
