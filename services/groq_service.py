"""Tasks 4, 5, 6: Streaming, multi-model router, context with auto-summarization."""
import sqlite3
import logging
from groq import AsyncGroq
from utils.tokens import count_messages_tokens, count_tokens

logger = logging.getLogger(__name__)

TASK_KEYWORDS_COMPLEX = [
    "напиши", "написать", "реферат", "эссе", "сочинение", "объясни", "расскажи",
    "проанализируй", "сравни", "докажи", "describe", "explain", "write", "analyze",
    "жаз", "талда", "сипатта",
]


def _is_complex_task(text: str) -> bool:
    lower = text.lower()
    return len(text) > 150 or any(kw in lower for kw in TASK_KEYWORDS_COMPLEX)


class GroqService:
    def __init__(self, settings):
        self.settings = settings
        self.client = AsyncGroq(api_key=settings.groq_api_key, timeout=30.0)
        self.init_db()

    def init_db(self):
        with sqlite3.connect(self.settings.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    role TEXT,
                    content TEXT
                )
            """)
            conn.commit()

    def get_user_history(self, user_id: int) -> list[dict]:
        with sqlite3.connect(self.settings.db_path) as conn:
            rows = conn.execute(
                "SELECT role, content FROM history WHERE user_id = ? ORDER BY id DESC LIMIT 40",
                (user_id,),
            ).fetchall()
        return [{"role": r, "content": c} for r, c in reversed(rows)]

    def save_message(self, user_id: int, role: str, content: str):
        with sqlite3.connect(self.settings.db_path) as conn:
            conn.execute(
                "INSERT INTO history (user_id, role, content) VALUES (?, ?, ?)",
                (user_id, role, content),
            )
            conn.commit()

    def clear_history(self, user_id: int):
        with sqlite3.connect(self.settings.db_path) as conn:
            conn.execute("DELETE FROM history WHERE user_id = ?", (user_id,))
            conn.commit()

    async def _summarize_history(self, history: list[dict]) -> str:
        """Auto-summarize old messages when context window is exceeded (Task 6)."""
        text = "\n".join(f"{m['role']}: {m['content']}" for m in history)
        prompt = [
            {"role": "system", "content": "Сделай краткое резюме диалога (3-5 предложений) на том языке, на котором написан диалог."},
            {"role": "user", "content": text},
        ]
        response = await self.client.chat.completions.create(
            messages=prompt,
            model=self.settings.default_model,
            max_tokens=512,
        )
        return response.choices[0].message.content

    def _pick_model(self, text: str) -> str:
        """Task 5: Multi-model router."""
        if _is_complex_task(text):
            return self.settings.complex_model
        return self.settings.default_model

    async def get_ai_stream_response(self, user_id: int, user_text: str, model: str | None = None):
        """Task 4: Streaming with debounce. Task 6: auto-summarization."""
        self.save_message(user_id, "user", user_text)
        history = self.get_user_history(user_id)

        chosen_model = model or self._pick_model(user_text)
        logger.info(f"user={user_id} model={chosen_model} chars={len(user_text)}")

        system_msg = {
            "role": "system",
            "content": (
                "Ты профессиональный академический AI-ассистент для студентов Satbayev University. "
                "Ты в совершенстве владеешь казахским и русским языками. "
                "ОБЯЗАТЕЛЬНО отвечай строго на том языке, на котором к тебе обратился пользователь! "
                "Если пользователь пишет на казахском — отвечай на казахском. "
                "Пиши развернуто и подробно."
            ),
        }

        # Task 6: Auto-summarize if context too large
        token_count = count_messages_tokens(history)
        if token_count > self.settings.context_max_tokens and len(history) > 4:
            half = len(history) // 2
            old_part = history[:half]
            recent_part = history[half:]
            try:
                summary = await self._summarize_history(old_part)
                history = [{"role": "system", "content": f"[Краткое резюме предыдущего диалога]: {summary}"}] + recent_part
                logger.info(f"user={user_id} история авто-суммирована, было {token_count} токенов")
            except Exception as e:
                logger.warning(f"Не удалось суммировать историю: {e}")

        messages_to_send = [system_msg] + history

        # Task 5: Fallback chain
        models_to_try = [chosen_model]
        if chosen_model != self.settings.default_model:
            models_to_try.append(self.settings.default_model)

        last_error = None
        for attempt_model in models_to_try:
            try:
                stream = await self.client.chat.completions.create(
                    messages=messages_to_send,
                    model=attempt_model,
                    stream=True,
                )
                full_reply = ""
                async for chunk in stream:
                    if chunk.choices and chunk.choices[0].delta and chunk.choices[0].delta.content:
                        full_reply += chunk.choices[0].delta.content
                        yield full_reply

                if full_reply.strip():
                    self.save_message(user_id, "assistant", full_reply)
                    logger.info(f"user={user_id} ответ {len(full_reply)} символов model={attempt_model}")
                return
            except Exception as e:
                last_error = e
                logger.warning(f"Модель {attempt_model} недоступна: {e}, переключаюсь на следующую")

        raise RuntimeError(f"Все модели недоступны: {last_error}")

    async def get_simple_response(self, messages: list[dict], model: str | None = None) -> str:
        """Non-streaming call for internal use (summarization, eval, etc)."""
        m = model or self.settings.default_model
        response = await self.client.chat.completions.create(
            messages=messages,
            model=m,
        )
        return response.choices[0].message.content

    async def translate_prompt(self, raw_prompt: str, system_prompt: str) -> str:
        """Translate/sanitize any-language prompt to English for image generators."""
        result = await self.get_simple_response(
            [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": raw_prompt},
            ],
            model="llama-3.1-8b-instant",
        )
        return result.strip().strip('"').strip("'")

    async def transcribe_audio(self, audio_bytes: bytes, filename: str = "audio.wav") -> str:
        """Task 18: Whisper transcription."""
        import io
        audio_file = io.BytesIO(audio_bytes)
        audio_file.name = filename
        transcription = await self.client.audio.transcriptions.create(
            file=(filename, audio_bytes),
            model=self.settings.audio_model,
            response_format="text",
        )
        return transcription
