"""Task 13: Private/Ollama mode handler."""
import logging
import time
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message
from services.ollama_service import OllamaService
from services.groq_service import GroqService
from services.rate_limiter import InMemoryRateLimiter

logger = logging.getLogger(__name__)
router = Router()

# In-memory set of users in private mode
_private_mode_users: set[int] = set()


def is_private_mode(user_id: int) -> bool:
    return user_id in _private_mode_users


@router.message(Command("private"))
async def cmd_private(message: Message, ollama_service: OllamaService):
    if not await ollama_service.is_available():
        await message.answer(
            "⚠️ Ollama недоступна. Запустите локальный сервер:\n"
            "<code>ollama serve</code>",
            parse_mode="HTML",
        )
        return
    _private_mode_users.add(message.from_user.id)
    await message.answer(
        "🔒 <b>Приватный режим включён</b>\n"
        f"Используется локальная модель: <code>{ollama_service.default_model}</code>\n"
        "Сообщения не уходят в облако.\n\n"
        "Для возврата: /cloud",
        parse_mode="HTML",
    )


@router.message(Command("cloud"))
async def cmd_cloud(message: Message):
    _private_mode_users.discard(message.from_user.id)
    await message.answer("☁️ <b>Облачный режим (Groq) включён.</b>", parse_mode="HTML")


@router.message(F.text & ~F.text.startswith('/'), lambda msg: is_private_mode(msg.from_user.id))
async def handle_private_message(
    message: Message,
    ollama_service: OllamaService,
    rate_limiter: InMemoryRateLimiter,
):
    user_id = message.from_user.id
    allowed, reason = await rate_limiter.check(user_id, message.chat.id)
    if not allowed:
        await message.answer(f"⏳ {reason}")
        return

    sent = await message.answer("🔒 <i>Генерирую локально...</i>", parse_mode="HTML")
    last_update = 0.0
    final_text = ""

    try:
        messages = [
            {"role": "system", "content": "Ты вежливый помощник-ассистент студента."},
            {"role": "user", "content": message.text},
        ]
        async for chunk in ollama_service.chat_stream(messages):
            final_text = chunk
            now = time.time()
            if now - last_update >= 1.4:
                try:
                    await sent.edit_text(f"🔒 {final_text}")
                    last_update = now
                except Exception:
                    pass

        if final_text:
            try:
                await sent.edit_text(f"🔒 {final_text}")
            except Exception:
                pass
    except Exception as e:
        logger.exception(f"Ошибка Ollama: {e}")
        await sent.edit_text("⚠️ Локальная модель недоступна. Используйте /cloud для переключения.")
