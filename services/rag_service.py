"""Task 14: RAG pipeline with pgvector + Ollama embeddings."""
import logging
from typing import Optional

logger = logging.getLogger(__name__)

try:
    import asyncpg
    _PG_AVAILABLE = True
except ImportError:
    _PG_AVAILABLE = False


class RagService:
    def __init__(self, settings, ollama_service):
        self.settings = settings
        self.ollama = ollama_service
        self._pool: Optional[object] = None

    async def init_pool(self):
        if not _PG_AVAILABLE:
            logger.warning("asyncpg не установлен, RAG недоступен")
            return
        try:
            self._pool = await asyncpg.create_pool(self.settings.postgres_dsn, min_size=1, max_size=5)
            async with self._pool.acquire() as conn:
                await conn.execute("CREATE EXTENSION IF NOT EXISTS vector")
                await conn.execute("""
                    CREATE TABLE IF NOT EXISTS documents (
                        id SERIAL PRIMARY KEY,
                        content TEXT,
                        embedding vector(768),
                        source TEXT,
                        created_at TIMESTAMPTZ DEFAULT NOW()
                    )
                """)
                await conn.execute("""
                    CREATE INDEX IF NOT EXISTS documents_embedding_idx
                    ON documents USING ivfflat (embedding vector_cosine_ops)
                    WITH (lists = 100)
                """)
            logger.info("RAG: PostgreSQL pool инициализирован")
        except Exception as e:
            logger.warning(f"RAG: PostgreSQL недоступен ({e}), сервис отключён")
            self._pool = None

    async def add_document(self, content: str, source: str = "manual"):
        if not self._pool:
            raise RuntimeError("PostgreSQL недоступен")
        embedding = await self.ollama.embed(content)
        async with self._pool.acquire() as conn:
            await conn.execute(
                "INSERT INTO documents (content, embedding, source) VALUES ($1, $2, $3)",
                content,
                str(embedding),
                source,
            )

    async def search(self, query: str, top_k: int = 5) -> list[dict]:
        if not self._pool:
            return []
        try:
            embedding = await self.ollama.embed(query)
            async with self._pool.acquire() as conn:
                rows = await conn.fetch(
                    """
                    SELECT content, source, 1 - (embedding <=> $1::vector) AS similarity
                    FROM documents
                    ORDER BY embedding <=> $1::vector
                    LIMIT $2
                    """,
                    str(embedding),
                    top_k,
                )
            return [{"content": r["content"], "source": r["source"], "score": r["similarity"]} for r in rows]
        except Exception as e:
            logger.error(f"RAG search error: {e}")
            return []

    async def rag_answer(self, question: str, groq_service) -> str:
        docs = await self.search(question)
        if not docs:
            return None

        context = "\n\n".join(
            f"[Источник: {d['source']}]\n{d['content']}" for d in docs
        )
        messages = [
            {
                "role": "system",
                "content": (
                    "Ты академический ассистент. Используй предоставленный контекст для ответа. "
                    "Указывай источники. Если в контексте нет ответа — скажи об этом."
                ),
            },
            {
                "role": "user",
                "content": f"Контекст:\n{context}\n\nВопрос: {question}",
            },
        ]
        return await groq_service.get_simple_response(messages)
