"""Tasks 13-17: Ollama integration — hybrid mode, RAG embeddings, benchmark, function calling, dynamic model loading."""
import asyncio
import logging
import time
from dataclasses import dataclass

import httpx

logger = logging.getLogger(__name__)


@dataclass
class BenchmarkResult:
    model: str
    question: str
    answer: str
    latency_ms: float
    tokens_per_sec: float
    error: str = ""


class OllamaService:
    def __init__(self, settings):
        self.host = settings.ollama_host
        self.default_model = settings.ollama_default_model
        self._client = httpx.AsyncClient(base_url=self.host, timeout=120.0)

    async def is_available(self) -> bool:
        try:
            r = await self._client.get("/api/tags")
            return r.status_code == 200
        except Exception:
            return False

    async def list_models(self) -> list[str]:
        r = await self._client.get("/api/tags")
        r.raise_for_status()
        return [m["name"] for m in r.json().get("models", [])]

    async def generate_stream(self, prompt: str, model: str | None = None):
        """Task 13: stream text from local Ollama model."""
        m = model or self.default_model
        payload = {"model": m, "prompt": prompt, "stream": True}
        full_text = ""
        async with self._client.stream("POST", "/api/generate", json=payload) as resp:
            resp.raise_for_status()
            async for line in resp.aiter_lines():
                if not line:
                    continue
                import json
                data = json.loads(line)
                if data.get("response"):
                    full_text += data["response"]
                    yield full_text
                if data.get("done"):
                    break

    async def chat_stream(self, messages: list[dict], model: str | None = None):
        """Chat-compatible streaming for Ollama."""
        import json
        m = model or self.default_model
        payload = {"model": m, "messages": messages, "stream": True}
        full_text = ""
        async with self._client.stream("POST", "/api/chat", json=payload) as resp:
            resp.raise_for_status()
            async for line in resp.aiter_lines():
                if not line:
                    continue
                data = json.loads(line)
                content = data.get("message", {}).get("content", "")
                if content:
                    full_text += content
                    yield full_text
                if data.get("done"):
                    break

    async def embed(self, text: str, model: str = "nomic-embed-text") -> list[float]:
        """Task 14: Generate embeddings via Ollama."""
        r = await self._client.post("/api/embed", json={"model": model, "input": text})
        r.raise_for_status()
        data = r.json()
        return data.get("embeddings", [[]])[0]

    async def function_call(self, messages: list[dict], tools: list[dict], model: str | None = None) -> dict:
        """Task 16: Function calling via Ollama."""
        import json
        m = model or self.default_model
        payload = {"model": m, "messages": messages, "tools": tools, "stream": False}
        r = await self._client.post("/api/chat", json=payload)
        r.raise_for_status()
        return r.json()

    async def pull_model(self, model_name: str):
        """Task 17: Pull a model with progress updates (async generator)."""
        import json
        payload = {"name": model_name, "stream": True}
        async with self._client.stream("POST", "/api/pull", json=payload) as resp:
            resp.raise_for_status()
            async for line in resp.aiter_lines():
                if not line:
                    continue
                data = json.loads(line)
                status = data.get("status", "")
                total = data.get("total", 0)
                completed = data.get("completed", 0)
                pct = int(completed / total * 100) if total else 0
                yield status, pct, data.get("error", "")
                if data.get("status") == "success":
                    break

    async def benchmark_question(self, question: str, model: str | None = None) -> BenchmarkResult:
        """Task 15: Benchmark a single question."""
        m = model or self.default_model
        start = time.perf_counter()
        answer = ""
        token_count = 0
        try:
            async for text in self.generate_stream(question, model=m):
                answer = text
            elapsed = time.perf_counter() - start
            token_count = len(answer.split())
            latency_ms = elapsed * 1000
            tps = token_count / elapsed if elapsed > 0 else 0
            return BenchmarkResult(m, question, answer, latency_ms, tps)
        except Exception as e:
            elapsed = time.perf_counter() - start
            return BenchmarkResult(m, question, "", elapsed * 1000, 0, str(e))

    async def warm_up(self, model: str | None = None):
        """Pre-warm a model so it's loaded into memory."""
        m = model or self.default_model
        try:
            async for _ in self.generate_stream("Hello", model=m):
                break
        except Exception as e:
            logger.warning(f"Warm-up failed for {m}: {e}")
