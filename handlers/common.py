"""Tasks 0.1-0.5, 1: Main message handler with /start, /help, rate limiting, logging, error handling."""
import logging
import time
import psycopg2
from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message
from services.groq_service import GroqService
from services.rate_limiter import InMemoryRateLimiter

logger = logging.getLogger(__name__)
router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message):
    """Task 0.2: /start with user name."""
    name = message.from_user.first_name or "друг"
    await message.answer(
        f"👋 Привет, <b>{name}</b>!\n\n"
        "Я — академический AI-ассистент студентов <b>Satbayev University</b>.\n"
        "Пиши тему эссе, задавай вопросы — отвечу на русском и казахском.\n\n"
        "Напиши /help чтобы увидеть все команды.",
        parse_mode="HTML",
    )


@router.message(Command("help"))
async def cmd_help(message: Message):
    """Task 0.2: /help with formatted HTML."""
    text = (
        "📚 <b>Доступные команды:</b>\n\n"
        "🤖 <b>Основное</b>\n"
        "  /start — начать работу\n"
        "  /help — список команд\n"
        "  /clear — очистить историю диалога\n\n"
        "🔒 <b>Приватный режим (Ollama)</b>\n"
        "  /private — переключиться на локальную модель\n"
        "  /cloud — вернуться на Groq\n\n"
        "🔍 <b>Поиск и данные</b>\n"
        "  /search &lt;запрос&gt; — поиск в интернете\n"
        "  /ask &lt;вопрос&gt; — RAG-поиск по документам\n\n"
        "🖼 <b>Медиа</b>\n"
        "  /imagine &lt;описание&gt; — генерация изображения\n"
        "  (или отправь фото — бот его опишет)\n"
        "  (или отправь голосовое — бот транскрибирует)\n\n"
        "📅 <b>Google Calendar</b>\n"
        "  /connect_calendar — привязать Google-аккаунт\n"
        "  /calendar_code &lt;код&gt; — ввести код авторизации\n\n"
        "⚙️ <b>Техническое</b>\n"
        "  /files — список файлов (MCP)\n"
        "  /benchmark — сравнить Groq vs Ollama\n"
        "  /model pull &lt;имя&gt; — скачать модель Ollama (admin)\n\n"
        "📊 <b>История и статистика</b>\n"
        "  /history — последние 10 сообщений\n"
        "  /stats — статистика базы данных\n"
    )
    await message.answer(text, parse_mode="HTML")


@router.message(Command("clear"))
async def cmd_clear(message: Message, groq_service: GroqService):
    groq_service.clear_history(message.from_user.id)
    await message.answer("🗑 История диалога очищена.")


@router.message(F.text & ~F.text.startswith('/'))
async def handle_ai_message(message: Message, groq_service: GroqService, rate_limiter: InMemoryRateLimiter):
    user_id = message.from_user.id
    chat_id = message.chat.id
    user_text = message.text.strip()

    if not user_text:
        return

    # Task 3: rate limiting
    allowed, reason = await rate_limiter.check(user_id, chat_id)
    if not allowed:
        await message.answer(f"⏳ {reason}")
        return

    sent = await message.answer("🤖 <i>Генерирую ответ...</i>", parse_mode="HTML")
    last_update = 0.0
    final_text = ""

    try:
        async for chunk in groq_service.get_ai_stream_response(user_id, user_text):
            final_text = chunk
            now = time.time()
            # Task 4: debounce — не чаще 1.4с
            if now - last_update >= 1.4:
                try:
                    await sent.edit_text(final_text)
                    last_update = now
                except Exception:
                    pass

        if final_text:
            try:
                await sent.edit_text(final_text)
            except Exception:
                pass

        # Task 0.4: log user action
        logger.info(
            "message handled",
            extra={
                "user_id": user_id,
                "username": message.from_user.username,
                "text": user_text[:100],
                "response_len": len(final_text),
            },
        )

        # Save to PostgreSQL for pgAdmin monitoring
        try:
            pg_dsn = groq_service.settings.postgres_dsn
            conn = psycopg2.connect(pg_dsn, connect_timeout=3)
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO bot_messages (user_id, username, first_name, message_text, bot_response) VALUES (%s,%s,%s,%s,%s)",
                (user_id, message.from_user.username, message.from_user.first_name, user_text[:2000], final_text[:2000])
            )
            conn.commit()
            conn.close()
        except Exception as pg_err:
            logger.warning(f"PostgreSQL save failed (non-critical): {pg_err}")

    except Exception as e:
        logger.exception(f"Ошибка при генерации ответа: {e}")
        try:
            # Task 0.5: human-readable error
            await sent.edit_text("⚠️ Сервис временно недоступен, попробуйте через минуту.")
        except Exception:
            pass
