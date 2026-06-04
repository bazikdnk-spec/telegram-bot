"""Task 24: Integration-style scenario tests (mocked Telegram + real service logic)."""
import pytest
import sqlite3
import time
from unittest.mock import AsyncMock, MagicMock, patch


async def _make_full_context(tmp_path):
    """Create a real GroqService + InMemoryRateLimiter for integration tests."""
    from services.groq_service import GroqService
    from services.rate_limiter import InMemoryRateLimiter
    from unittest.mock import MagicMock

    settings = MagicMock()
    settings.db_path = str(tmp_path / "integration.db")
    settings.default_model = "llama-3.1-8b-instant"
    settings.complex_model = "llama-3.3-70b-versatile"
    settings.context_max_tokens = 6000

    with patch("services.groq_service.AsyncGroq"):
        groq = GroqService(settings=settings)

    rate_limiter = InMemoryRateLimiter(10, 50, 30)
    return groq, rate_limiter, settings


class TestScenario1StartAndHelp:
    async def test_start_then_help_flow(self, tmp_path):
        groq, rate_limiter, settings = await _make_full_context(tmp_path)
        msg = MagicMock()
        msg.from_user.id = 100
        msg.from_user.first_name = "Алибек"
        msg.from_user.username = "alibek"
        msg.chat.id = 100
        msg.answer = AsyncMock()

        from handlers.common import cmd_start, cmd_help
        await cmd_start(msg)
        assert msg.answer.called
        start_text = msg.answer.call_args[0][0]
        assert "Алибек" in start_text

        msg.answer.reset_mock()
        await cmd_help(msg)
        help_text = msg.answer.call_args[0][0]
        assert "/private" in help_text
        assert "/search" in help_text


class TestScenario2RateLimiting:
    async def test_user_gets_blocked_after_limit(self, tmp_path):
        from services.rate_limiter import InMemoryRateLimiter
        limiter = InMemoryRateLimiter(3, 100, 100)
        results = []
        for _ in range(5):
            ok, _ = await limiter.check(200, 200)
            results.append(ok)
        assert results[:3] == [True, True, True]
        assert results[3] == False
        assert results[4] == False


class TestScenario3HistoryIsolation:
    async def test_two_users_separate_histories(self, tmp_path):
        groq, rate_limiter, settings = await _make_full_context(tmp_path)
        groq.save_message(1, "user", "Привет от пользователя 1")
        groq.save_message(1, "assistant", "Ответ пользователю 1")
        groq.save_message(2, "user", "Сообщение пользователя 2")

        h1 = groq.get_user_history(1)
        h2 = groq.get_user_history(2)
        assert len(h1) == 2
        assert len(h2) == 1
        assert h2[0]["content"] == "Сообщение пользователя 2"


class TestScenario4ClearHistory:
    async def test_clear_removes_all_messages(self, tmp_path):
        groq, _, settings = await _make_full_context(tmp_path)
        for i in range(5):
            groq.save_message(3, "user", f"Сообщение {i}")
        assert len(groq.get_user_history(3)) == 5
        groq.clear_history(3)
        assert groq.get_user_history(3) == []


class TestScenario5MultiModelRouter:
    async def test_simple_question_uses_fast_model(self, tmp_path):
        groq, _, settings = await _make_full_context(tmp_path)
        model = groq._pick_model("Привет!")
        assert model == settings.default_model

    async def test_essay_request_uses_complex_model(self, tmp_path):
        groq, _, settings = await _make_full_context(tmp_path)
        model = groq._pick_model("Напиши эссе о роли технологий в современном образовании")
        assert model == settings.complex_model

    async def test_kazakh_essay_request_uses_complex_model(self, tmp_path):
        groq, _, settings = await _make_full_context(tmp_path)
        model = groq._pick_model("Эссе жазып берші")
        assert model == settings.complex_model


class TestScenario6SearchFormatting:
    def test_search_results_numbered(self):
        from services.search_service import SearchService
        svc = SearchService(settings=MagicMock())
        results = [
            {"title": "Первый", "url": "http://a.com", "snippet": "Описание первого"},
            {"title": "Второй", "url": "http://b.com", "snippet": "Описание второго"},
        ]
        text = svc.format_results(results)
        assert "1." in text
        assert "2." in text
        assert "Первый" in text
        assert "Второй" in text


class TestScenario7TokenCounting:
    def test_empty_history_zero_tokens(self):
        from utils.tokens import count_messages_tokens
        assert count_messages_tokens([]) == 0

    def test_growing_history_grows_tokens(self):
        from utils.tokens import count_messages_tokens
        msgs1 = [{"role": "user", "content": "Hello"}]
        msgs2 = [{"role": "user", "content": "Hello"}, {"role": "assistant", "content": "Hi there!"}]
        assert count_messages_tokens(msgs2) > count_messages_tokens(msgs1)


class TestScenario8CalendarEncryption:
    def test_encrypted_token_not_readable(self, tmp_path):
        from services.calendar_service import CalendarService
        from cryptography.fernet import Fernet
        settings = MagicMock()
        settings.db_path = str(tmp_path / "cal.db")
        settings.fernet_key = Fernet.generate_key().decode()
        svc = CalendarService(settings)
        secret = '{"access_token": "super_secret_123"}'
        encrypted = svc._encrypt(secret)
        assert "super_secret_123" not in encrypted
        assert svc._decrypt(encrypted) == secret


class TestScenario9BenchmarkResultStructure:
    async def test_benchmark_result_has_required_fields(self):
        from services.ollama_service import BenchmarkResult
        result = BenchmarkResult(
            model="test-model",
            question="Test?",
            answer="Answer",
            latency_ms=100.0,
            tokens_per_sec=10.5,
        )
        assert result.model == "test-model"
        assert result.latency_ms == 100.0
        assert result.error == ""


class TestScenario10CommandParsing:
    async def test_imagine_without_prompt_sends_usage(self):
        from handlers.image_handler import handle_imagine
        from aiogram.filters.command import CommandObject
        msg = MagicMock()
        msg.from_user.id = 1
        msg.chat.id = 1
        msg.text = "/imagine"
        msg.answer = AsyncMock()
        command = MagicMock(spec=CommandObject)
        command.args = None
        groq_service = MagicMock()
        image_service = MagicMock()
        rate_limiter = MagicMock()
        rate_limiter.check = AsyncMock(return_value=(True, ""))
        await handle_imagine(msg, command, groq_service, image_service, rate_limiter)
        assert msg.answer.called

    async def test_search_without_query_sends_usage(self):
        from handlers.admin import cmd_search
        msg = MagicMock()
        msg.text = "/search"
        msg.answer = AsyncMock()
        search_service = MagicMock()
        await cmd_search(msg, search_service)
        assert "Использование" in msg.answer.call_args[0][0]

    async def test_model_pull_without_subcommand(self):
        from handlers.admin import cmd_model
        msg = MagicMock()
        msg.text = "/model"
        msg.answer = AsyncMock()
        ollama_service = MagicMock()
        await cmd_model(msg, ollama_service)
        assert "Использование" in msg.answer.call_args[0][0]


class TestScenario11PrivateMode:
    async def test_private_cmd_when_ollama_unavailable(self):
        from handlers.private import cmd_private
        msg = MagicMock()
        msg.from_user.id = 1
        msg.answer = AsyncMock()
        ollama = MagicMock()
        ollama.is_available = AsyncMock(return_value=False)
        await cmd_private(msg, ollama)
        text = msg.answer.call_args[0][0]
        assert "недоступна" in text.lower() or "ollama" in text.lower()

    async def test_cloud_cmd_exits_private_mode(self):
        from handlers.private import cmd_cloud, _private_mode_users
        msg = MagicMock()
        msg.from_user.id = 42
        msg.answer = AsyncMock()
        _private_mode_users.add(42)
        await cmd_cloud(msg)
        assert 42 not in _private_mode_users


class TestScenario12MiscCoverage:
    async def test_rate_limiter_chat_level_works(self):
        from services.rate_limiter import InMemoryRateLimiter
        limiter = InMemoryRateLimiter(100, 2, 100)
        await limiter.check(1, 999)
        await limiter.check(2, 999)
        ok, reason = await limiter.check(3, 999)
        assert not ok
        assert "чата" in reason

    async def test_rate_limiter_global_level_works(self):
        from services.rate_limiter import InMemoryRateLimiter
        limiter = InMemoryRateLimiter(100, 100, 2)
        await limiter.check(1, 1)
        await limiter.check(2, 2)
        ok, reason = await limiter.check(3, 3)
        assert not ok
        assert "глобальн" in reason.lower()

    async def test_cmd_ask_without_question(self):
        from handlers.mcp_handler import cmd_ask
        msg = MagicMock()
        msg.text = "/ask"
        msg.answer = AsyncMock()
        rag_service = MagicMock()
        groq_service = MagicMock()
        await cmd_ask(msg, rag_service, groq_service)
        assert "Использование" in msg.answer.call_args[0][0]
