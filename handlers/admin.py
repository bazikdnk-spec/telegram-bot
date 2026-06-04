"""Tasks 15, 17, 19, 21: Admin commands — benchmark, model pull, search, calendar."""
import logging
import sqlite3
import time
from datetime import datetime, timedelta, timezone

import openpyxl
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, BufferedInputFile
from services.groq_service import GroqService
from services.ollama_service import OllamaService
from services.search_service import SearchService
from services.calendar_service import CalendarService
from services.rate_limiter import InMemoryRateLimiter

logger = logging.getLogger(__name__)
router = Router()

BENCHMARK_QUESTIONS = [
    "Что такое машинное обучение?", "Объясни принцип работы нейронных сетей.",
    "Какова столица Казахстана?", "Что такое Python?", "Расскажи о Satbayev University.",
    "Как работает интернет?", "Что такое база данных?", "Объясни REST API.",
    "Что такое Docker?", "Как работает Git?",
    "Нейрон деген не?", "Жасанды интеллект туралы айт.", "Алгоритм дегеніміз не?",
    "Бағдарламалау тілдері қандай?", "Деректер базасы дегеніміз не?",
    "What is Kubernetes?", "Explain microservices.", "What is CI/CD?",
    "Explain async programming.", "What is a REST API?",
]


def _is_admin(user_id: int, settings) -> bool:
    return user_id in settings.get_admin_ids()


@router.message(Command("benchmark"))
async def cmd_benchmark(
    message: Message,
    groq_service: GroqService,
    ollama_service: OllamaService,
):
    """Task 15: Benchmark Groq vs Ollama, export to Excel."""
    sent = await message.answer("⏱ <b>Запускаю бенчмарк...</b>\nЭто займёт несколько минут.", parse_mode="HTML")

    questions = BENCHMARK_QUESTIONS[:5]  # Limit for demo; full is 20

    groq_results = []
    ollama_results = []
    ollama_available = await ollama_service.is_available()

    for i, q in enumerate(questions):
        await sent.edit_text(f"⏱ Тестирую... {i+1}/{len(questions)}")

        # Groq benchmark
        start = time.perf_counter()
        try:
            answer = await groq_service.get_simple_response(
                [{"role": "user", "content": q}]
            )
            elapsed = (time.perf_counter() - start) * 1000
            groq_results.append({"q": q, "latency_ms": elapsed, "tokens": len(answer.split()), "error": ""})
        except Exception as e:
            groq_results.append({"q": q, "latency_ms": 0, "tokens": 0, "error": str(e)})

        # Ollama benchmark
        if ollama_available:
            result = await ollama_service.benchmark_question(q)
            ollama_results.append({
                "q": q, "latency_ms": result.latency_ms,
                "tokens": result.tokens_per_sec, "error": result.error,
            })
        else:
            ollama_results.append({"q": q, "latency_ms": 0, "tokens": 0, "error": "Ollama unavailable"})

    # Build Excel report
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Benchmark"
    ws.append(["Question", "Groq Latency (ms)", "Groq Tokens", "Ollama Latency (ms)", "Ollama TPS"])
    for g, o in zip(groq_results, ollama_results):
        ws.append([g["q"][:50], round(g["latency_ms"]), g["tokens"], round(o["latency_ms"]), round(o["tokens"])])

    import io
    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)

    groq_avg = sum(r["latency_ms"] for r in groq_results if not r["error"]) / max(len(groq_results), 1)
    ollama_avg = sum(r["latency_ms"] for r in ollama_results if not r["error"]) / max(len(ollama_results), 1)

    summary = (
        f"📊 <b>Результаты бенчмарка ({len(questions)} вопросов)</b>\n\n"
        f"☁️ Groq avg latency: <b>{groq_avg:.0f} мс</b>\n"
        f"💻 Ollama avg latency: <b>{ollama_avg:.0f} мс</b>"
    )
    await sent.edit_text(summary, parse_mode="HTML")
    await message.answer_document(
        BufferedInputFile(buf.read(), filename="benchmark.xlsx"),
        caption="📊 Полный отчёт бенчмарка",
    )


@router.message(Command("model"))
async def cmd_model(message: Message, ollama_service: OllamaService):
    """Task 17: Admin command to pull Ollama model."""
    parts = message.text.split()
    if len(parts) < 3 or parts[1] != "pull":
        await message.answer("Использование: /model pull <имя_модели>")
        return

    model_name = parts[2]
    sent = await message.answer(f"📥 <i>Скачиваю модель {model_name}...</i>", parse_mode="HTML")
    last_update = 0.0

    try:
        async for status, pct, error in ollama_service.pull_model(model_name):
            if error:
                await sent.edit_text(f"❌ Ошибка: {error}")
                return
            now = time.time()
            if now - last_update >= 5.0:
                bar = "█" * (pct // 10) + "░" * (10 - pct // 10)
                await sent.edit_text(
                    f"📥 Скачиваю <code>{model_name}</code>...\n"
                    f"[{bar}] {pct}%\n<i>{status}</i>",
                    parse_mode="HTML",
                )
                last_update = now

        await sent.edit_text(f"✅ Модель <code>{model_name}</code> успешно загружена!", parse_mode="HTML")
        # Warm up
        await ollama_service.warm_up(model_name)
    except Exception as e:
        logger.exception(f"Ошибка загрузки модели: {e}")
        await sent.edit_text(f"❌ Ошибка загрузки: {e}")


@router.message(Command("search"))
async def cmd_search(message: Message, search_service: SearchService):
    """Task 19: Web search."""
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await message.answer("Использование: /search <запрос>")
        return

    query = parts[1]
    sent = await message.answer(f"🔍 <i>Ищу: {query}...</i>", parse_mode="HTML")
    try:
        results = await search_service.search(query)
        text = search_service.format_results(results)
        await sent.edit_text(f"🔍 <b>Результаты поиска:</b>\n\n{text}", parse_mode="HTML", disable_web_page_preview=True)
    except Exception as e:
        logger.exception(f"Ошибка поиска: {e}")
        await sent.edit_text("⚠️ Поиск временно недоступен.")


@router.message(Command("connect_calendar"))
async def cmd_connect_calendar(message: Message, calendar_service: CalendarService):
    """Task 21: Start Google Calendar OAuth2 flow."""
    auth_url = calendar_service.get_auth_url(message.from_user.id)
    if not auth_url:
        await message.answer("⚠️ Google Calendar недоступен. Проверьте GOOGLE_CREDENTIALS_FILE.")
        return
    await message.answer(
        f"📅 <b>Авторизация Google Calendar</b>\n\n"
        f"1. Перейдите по ссылке: {auth_url}\n"
        f"2. Разрешите доступ\n"
        f"3. Скопируйте код и отправьте: /calendar_code КОД",
        parse_mode="HTML",
        disable_web_page_preview=True,
    )


@router.message(Command("calendar_code"))
async def cmd_calendar_code(message: Message, calendar_service: CalendarService):
    """Task 21: Exchange OAuth2 code."""
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await message.answer("Использование: /calendar_code <код>")
        return
    code = parts[1].strip()
    success = calendar_service.exchange_code(message.from_user.id, code)
    if success:
        await message.answer("✅ Google Calendar успешно подключён!")
    else:
        await message.answer("❌ Неверный код или ошибка авторизации. Попробуйте /connect_calendar снова.")


@router.message(Command("stats"))
async def cmd_stats(message: Message, groq_service: GroqService):
    """Показывает статистику запросов из базы данных."""
    db_path = groq_service.settings.db_path
    try:
        with sqlite3.connect(db_path) as conn:
            # Общее количество сообщений
            total = conn.execute("SELECT COUNT(*) FROM history").fetchone()[0]
            # Количество уникальных пользователей
            users = conn.execute("SELECT COUNT(DISTINCT user_id) FROM history").fetchone()[0]
            # Количество сообщений пользователя
            user_msgs = conn.execute(
                "SELECT COUNT(*) FROM history WHERE user_id=? AND role='user'",
                (message.from_user.id,)
            ).fetchone()[0]
            # Топ 5 активных пользователей
            top = conn.execute(
                "SELECT user_id, COUNT(*) as cnt FROM history WHERE role='user' "
                "GROUP BY user_id ORDER BY cnt DESC LIMIT 5"
            ).fetchall()

        top_text = "\n".join(f"  👤 user_id <code>{uid}</code> — {cnt} сообщений" for uid, cnt in top)

        text = (
            "📊 <b>Статистика базы данных</b>\n\n"
            f"💬 Всего сообщений в БД: <b>{total}</b>\n"
            f"👥 Уникальных пользователей: <b>{users}</b>\n"
            f"🙋 Твоих сообщений: <b>{user_msgs}</b>\n\n"
            f"🏆 <b>Топ активных пользователей:</b>\n{top_text}"
        )
        await message.answer(text, parse_mode="HTML")
    except Exception as e:
        await message.answer(f"❌ Ошибка: {e}")


@router.message(Command("history"))
async def cmd_history(message: Message, groq_service: GroqService):
    """Показывает последние 10 сообщений текущего пользователя."""
    db_path = groq_service.settings.db_path
    user_id = message.from_user.id
    try:
        with sqlite3.connect(db_path) as conn:
            rows = conn.execute(
                "SELECT role, content FROM history WHERE user_id=? ORDER BY id DESC LIMIT 10",
                (user_id,)
            ).fetchall()

        if not rows:
            await message.answer("📭 История пуста. Напиши что-нибудь боту!")
            return

        lines = []
        for role, content in reversed(rows):
            icon = "🙋" if role == "user" else "🤖"
            # Обрезаем длинные сообщения
            short = content[:120] + "..." if len(content) > 120 else content
            lines.append(f"{icon} <b>{role}:</b> {short}")

        text = "📜 <b>Последние сообщения:</b>\n\n" + "\n\n".join(lines)
        await message.answer(text, parse_mode="HTML")
    except Exception as e:
        await message.answer(f"❌ Ошибка: {e}")
