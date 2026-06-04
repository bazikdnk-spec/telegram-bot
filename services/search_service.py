"""Task 19: Web search via Tavily/Serper with Redis caching."""
import hashlib
import json
import logging
import time
from typing import Optional

import httpx

logger = logging.getLogger(__name__)


class SearchService:
    CACHE_TTL = 3600  # 1 hour

    def __init__(self, settings, redis_client=None):
        self.settings = settings
        self._redis = redis_client
        self._client = httpx.AsyncClient(timeout=15.0)

    async def _cache_get(self, key: str) -> Optional[list]:
        if not self._redis:
            return None
        try:
            data = await self._redis.get(f"search:{key}")
            return json.loads(data) if data else None
        except Exception:
            return None

    async def _cache_set(self, key: str, value: list):
        if not self._redis:
            return
        try:
            await self._redis.setex(f"search:{key}", self.CACHE_TTL, json.dumps(value, ensure_ascii=False))
        except Exception:
            pass

    def _cache_key(self, query: str) -> str:
        return hashlib.md5(query.encode()).hexdigest()

    async def search(self, query: str, num_results: int = 5) -> list[dict]:
        """Returns list of {title, url, snippet}."""
        cache_key = self._cache_key(query)
        cached = await self._cache_get(cache_key)
        if cached:
            logger.info(f"Search cache hit: {query[:50]}")
            return cached

        if self.settings.search_provider == "tavily":
            results = await self._tavily_search(query, num_results)
        else:
            results = await self._serper_search(query, num_results)

        await self._cache_set(cache_key, results)
        return results

    async def _tavily_search(self, query: str, num_results: int) -> list[dict]:
        if not self.settings.search_api_key:
            return []
        payload = {
            "api_key": self.settings.search_api_key,
            "query": query,
            "max_results": num_results,
            "search_depth": "basic",
        }
        r = await self._client.post("https://api.tavily.com/search", json=payload)
        r.raise_for_status()
        return [
            {"title": item.get("title", ""), "url": item.get("url", ""), "snippet": item.get("content", "")}
            for item in r.json().get("results", [])
        ]

    async def _serper_search(self, query: str, num_results: int) -> list[dict]:
        if not self.settings.search_api_key:
            return []
        headers = {"X-API-KEY": self.settings.search_api_key, "Content-Type": "application/json"}
        payload = {"q": query, "num": num_results}
        r = await self._client.post("https://google.serper.dev/search", json=payload, headers=headers)
        r.raise_for_status()
        return [
            {"title": item.get("title", ""), "url": item.get("link", ""), "snippet": item.get("snippet", "")}
            for item in r.json().get("organic", [])
        ]

    def format_results(self, results: list[dict]) -> str:
        if not results:
            return "Поиск не дал результатов."
        lines = []
        for i, r in enumerate(results, 1):
            lines.append(f"{i}. <b>{r['title']}</b>\n{r['snippet']}\n🔗 {r['url']}")
        return "\n\n".join(lines)
