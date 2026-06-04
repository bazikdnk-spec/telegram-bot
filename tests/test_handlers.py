"""Task 23: Unit tests for all handlers with mocked external APIs."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


class TestCmdStart:
    async def test_start_greets_user(self, mock_message):
        from handlers.common import cmd_start
        await cmd_start(mock_message)
        mock_message.answer.assert_called_once()
        call_args = mock_message.answer.call_args[0][0]
        assert "Тест" in call_args
        assert "Satbayev" in call_args

    async def test_start_uses_html_parse_mode(self, mock_message):
        from handlers.common import cmd_start
        await cmd_start(mock_message)
        kwargs = mock_message.answer.call_args[1]
        assert kwargs.get("parse_mode") == "HTML"


class TestCmdHelp:
    async def test_help_contains_commands(self, mock_message):
        from handlers.common import cmd_help
        await cmd_help(mock_message)
        call_args = mock_message.answer.call_args[0][0]
        assert "/start" in call_args
        assert "/help" in call_args
        assert "/private" in call_args

    async def test_help_uses_html(self, mock_message):
        from handlers.common import cmd_help
        await cmd_help(mock_message)
        kwargs = mock_message.answer.call_args[1]
        assert kwargs.get("parse_mode") == "HTML"


class TestCmdClear:
    async def test_clear_calls_clear_history(self, mock_message, mock_groq_service):
        from handlers.common import cmd_clear
        await cmd_clear(mock_message, mock_groq_service)
        mock_groq_service.clear_history.assert_called_once_with(12345)

    async def test_clear_sends_confirmation(self, mock_message, mock_groq_service):
        from handlers.common import cmd_clear
        await cmd_clear(mock_message, mock_groq_service)
        mock_message.answer.assert_called_once()


class TestHandleAIMessage:
    async def test_rate_limit_blocks_user(self, mock_message, mock_groq_service, mock_rate_limiter):
        from handlers.common import handle_ai_message
        mock_rate_limiter.check = AsyncMock(return_value=(False, "Превышен лимит"))
        await handle_ai_message(mock_message, mock_groq_service, mock_rate_limiter)
        mock_message.answer.assert_called_once()
        assert "Превышен лимит" in mock_message.answer.call_args[0][0]

    async def test_empty_message_ignored(self, mock_message, mock_groq_service, mock_rate_limiter):
        from handlers.common import handle_ai_message
        mock_message.text = "   "
        await handle_ai_message(mock_message, mock_groq_service, mock_rate_limiter)
        mock_message.answer.assert_not_called()

    async def test_normal_message_gets_response(self, mock_message, mock_groq_service, mock_rate_limiter):
        from handlers.common import handle_ai_message
        mock_message.text = "Что такое Python?"
        sent = AsyncMock()
        sent.edit_text = AsyncMock()
        mock_message.answer = AsyncMock(return_value=sent)
        await handle_ai_message(mock_message, mock_groq_service, mock_rate_limiter)
        mock_message.answer.assert_called_once()

    async def test_groq_error_sends_user_message(self, mock_message, mock_groq_service, mock_rate_limiter):
        from handlers.common import handle_ai_message

        async def error_stream(*args, **kwargs):
            raise RuntimeError("API Error")
            yield  # make it a generator

        mock_groq_service.get_ai_stream_response = error_stream
        mock_message.text = "Привет"
        sent = AsyncMock()
        sent.edit_text = AsyncMock()
        mock_message.answer = AsyncMock(return_value=sent)
        await handle_ai_message(mock_message, mock_groq_service, mock_rate_limiter)
        sent.edit_text.assert_called_once()
        error_text = sent.edit_text.call_args[0][0]
        assert "недоступен" in error_text.lower() or "ошибка" in error_text.lower()


class TestRateLimiter:
    async def test_allows_within_limit(self):
        from services.rate_limiter import InMemoryRateLimiter
        limiter = InMemoryRateLimiter(10, 50, 30)
        for _ in range(5):
            ok, msg = await limiter.check(1, 1)
            assert ok

    async def test_blocks_over_limit(self):
        from services.rate_limiter import InMemoryRateLimiter
        limiter = InMemoryRateLimiter(3, 50, 30)
        for _ in range(3):
            await limiter.check(2, 2)
        ok, msg = await limiter.check(2, 2)
        assert not ok
        assert "лимит" in msg.lower()

    async def test_different_users_independent(self):
        from services.rate_limiter import InMemoryRateLimiter
        limiter = InMemoryRateLimiter(2, 50, 100)
        await limiter.check(10, 10)
        await limiter.check(10, 10)
        ok_blocked, _ = await limiter.check(10, 10)
        ok_other, _ = await limiter.check(20, 20)
        assert not ok_blocked
        assert ok_other


class TestTokenBucket:
    def test_initial_full(self):
        from services.rate_limiter import TokenBucket
        b = TokenBucket(capacity=10, refill_rate=1.0)
        assert b.consume()

    def test_depletes(self):
        from services.rate_limiter import TokenBucket
        b = TokenBucket(capacity=2, refill_rate=0.0)
        b.consume()
        b.consume()
        assert not b.consume()


class TestTokenCounter:
    def test_count_empty_string(self):
        from utils.tokens import count_tokens
        assert count_tokens("") == 0

    def test_count_nonempty(self):
        from utils.tokens import count_tokens
        count = count_tokens("Hello world this is a test sentence.")
        assert count > 0

    def test_count_messages(self):
        from utils.tokens import count_messages_tokens
        msgs = [{"role": "user", "content": "Hi"}, {"role": "assistant", "content": "Hello there!"}]
        total = count_messages_tokens(msgs)
        assert total > 0
