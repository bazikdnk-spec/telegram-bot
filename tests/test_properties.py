"""Task 25: Property-based tests using Hypothesis."""
import pytest
from hypothesis import given, settings as h_settings, strategies as st


class TestTokenCounterProperties:
    @given(st.text(max_size=4096))
    def test_count_tokens_never_crashes(self, text):
        from utils.tokens import count_tokens
        result = count_tokens(text)
        assert isinstance(result, int)
        assert result >= 0

    @given(st.text(max_size=4096))
    def test_count_tokens_returns_string(self, text):
        from utils.tokens import count_tokens
        result = count_tokens(text)
        assert result >= 0

    @given(st.lists(
        st.fixed_dictionaries({
            "role": st.sampled_from(["user", "assistant", "system"]),
            "content": st.text(max_size=500),
        }),
        max_size=20,
    ))
    def test_count_messages_tokens_never_crashes(self, messages):
        from utils.tokens import count_messages_tokens
        result = count_messages_tokens(messages)
        assert isinstance(result, int)
        assert result >= 0


class TestRateLimiterProperties:
    @given(st.integers(min_value=1, max_value=100))
    @h_settings(max_examples=20)
    async def test_rate_limiter_exact_capacity(self, capacity):
        from services.rate_limiter import InMemoryRateLimiter
        limiter = InMemoryRateLimiter(capacity, 1000, 1000)
        allowed_count = 0
        for _ in range(capacity + 5):
            ok, _ = await limiter.check(999, 999)
            if ok:
                allowed_count += 1
        assert allowed_count == capacity

    @given(st.integers(min_value=1, max_value=50), st.integers(min_value=1, max_value=50))
    @h_settings(max_examples=10)
    async def test_rate_limiter_different_users_dont_share_budget(self, user1_id, user2_id):
        from services.rate_limiter import InMemoryRateLimiter
        if user1_id == user2_id:
            return
        limiter = InMemoryRateLimiter(2, 1000, 1000)
        await limiter.check(user1_id, user1_id)
        await limiter.check(user1_id, user1_id)
        ok, _ = await limiter.check(user2_id, user2_id)
        assert ok


class TestSearchServiceProperties:
    @given(st.text(min_size=1, max_size=200))
    @h_settings(deadline=None)
    def test_cache_key_is_string(self, query):
        from services.search_service import SearchService
        from unittest.mock import MagicMock
        settings = MagicMock()
        svc = SearchService(settings=settings)
        key = svc._cache_key(query)
        assert isinstance(key, str)
        assert len(key) == 32  # MD5 hex

    @given(st.text(min_size=1, max_size=200))
    @h_settings(deadline=None)
    def test_cache_key_deterministic(self, query):
        from services.search_service import SearchService
        from unittest.mock import MagicMock
        svc = SearchService(settings=MagicMock())
        assert svc._cache_key(query) == svc._cache_key(query)

    @given(st.lists(
        st.fixed_dictionaries({
            "title": st.text(max_size=100),
            "url": st.text(max_size=200),
            "snippet": st.text(max_size=300),
        }),
        max_size=10,
    ))
    @h_settings(deadline=None)
    def test_format_results_never_crashes(self, results):
        from services.search_service import SearchService
        from unittest.mock import MagicMock
        svc = SearchService(settings=MagicMock())
        output = svc.format_results(results)
        assert isinstance(output, str)


class TestGroqModelRouterProperties:
    @given(st.text(max_size=4096))
    def test_pick_model_always_returns_valid_model(self, text):
        from services.groq_service import GroqService
        from unittest.mock import MagicMock, patch
        settings = MagicMock()
        settings.db_path = ":memory:"
        settings.default_model = "llama-3.1-8b-instant"
        settings.complex_model = "llama-3.3-70b-versatile"
        with patch("services.groq_service.AsyncGroq"):
            svc = GroqService(settings=settings)
        model = svc._pick_model(text)
        assert model in ("llama-3.1-8b-instant", "llama-3.3-70b-versatile")
