"""Task 23: Unit tests for services with mocked external dependencies."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch, call
import sqlite3


class TestGroqService:
    def _make_service(self, mock_settings):
        from services.groq_service import GroqService
        with patch("services.groq_service.AsyncGroq"):
            svc = GroqService(settings=mock_settings)
        return svc

    def test_init_creates_db(self, mock_settings, tmp_path):
        from services.groq_service import GroqService
        mock_settings.db_path = str(tmp_path / "test.db")
        with patch("services.groq_service.AsyncGroq"):
            svc = GroqService(settings=mock_settings)
        with sqlite3.connect(mock_settings.db_path) as conn:
            tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
        assert any("history" in t[0] for t in tables)

    def test_save_and_get_history(self, mock_settings, tmp_path):
        from services.groq_service import GroqService
        mock_settings.db_path = str(tmp_path / "test.db")
        with patch("services.groq_service.AsyncGroq"):
            svc = GroqService(settings=mock_settings)
        svc.save_message(1, "user", "Hello")
        svc.save_message(1, "assistant", "Hi there!")
        history = svc.get_user_history(1)
        assert len(history) == 2
        assert history[0]["role"] == "user"
        assert history[0]["content"] == "Hello"

    def test_clear_history(self, mock_settings, tmp_path):
        from services.groq_service import GroqService
        mock_settings.db_path = str(tmp_path / "test.db")
        with patch("services.groq_service.AsyncGroq"):
            svc = GroqService(settings=mock_settings)
        svc.save_message(1, "user", "Test")
        svc.clear_history(1)
        assert svc.get_user_history(1) == []

    def test_pick_model_short_text(self, mock_settings, tmp_path):
        from services.groq_service import GroqService
        mock_settings.db_path = str(tmp_path / "test.db")
        with patch("services.groq_service.AsyncGroq"):
            svc = GroqService(settings=mock_settings)
        model = svc._pick_model("Привет")
        assert model == mock_settings.default_model

    def test_pick_model_complex_task(self, mock_settings, tmp_path):
        from services.groq_service import GroqService
        mock_settings.db_path = str(tmp_path / "test.db")
        with patch("services.groq_service.AsyncGroq"):
            svc = GroqService(settings=mock_settings)
        model = svc._pick_model("Напиши развернутое эссе о влиянии технологий на образование")
        assert model == mock_settings.complex_model

    def test_history_isolated_per_user(self, mock_settings, tmp_path):
        from services.groq_service import GroqService
        mock_settings.db_path = str(tmp_path / "test.db")
        with patch("services.groq_service.AsyncGroq"):
            svc = GroqService(settings=mock_settings)
        svc.save_message(1, "user", "User 1 message")
        svc.save_message(2, "user", "User 2 message")
        assert len(svc.get_user_history(1)) == 1
        assert len(svc.get_user_history(2)) == 1
        assert svc.get_user_history(1)[0]["content"] == "User 1 message"


class TestSearchService:
    async def test_returns_empty_without_key(self, mock_settings):
        from services.search_service import SearchService
        mock_settings.search_api_key = ""
        svc = SearchService(settings=mock_settings)
        results = await svc.search("test query")
        assert results == []

    def test_format_results_empty(self, mock_settings):
        from services.search_service import SearchService
        svc = SearchService(settings=mock_settings)
        text = svc.format_results([])
        assert "результат" in text.lower()

    def test_format_results_nonempty(self, mock_settings):
        from services.search_service import SearchService
        svc = SearchService(settings=mock_settings)
        results = [{"title": "Test", "url": "http://example.com", "snippet": "Test snippet"}]
        text = svc.format_results(results)
        assert "Test" in text
        assert "http://example.com" in text

    def test_cache_key_deterministic(self, mock_settings):
        from services.search_service import SearchService
        svc = SearchService(settings=mock_settings)
        assert svc._cache_key("hello") == svc._cache_key("hello")
        assert svc._cache_key("hello") != svc._cache_key("world")


class TestCalendarService:
    def test_encrypt_decrypt(self, mock_settings):
        from services.calendar_service import CalendarService
        from cryptography.fernet import Fernet
        mock_settings.fernet_key = Fernet.generate_key().decode()
        svc = CalendarService(mock_settings)
        original = '{"token": "test123"}'
        encrypted = svc._encrypt(original)
        assert encrypted != original
        assert svc._decrypt(encrypted) == original

    def test_no_key_passthrough(self, mock_settings, tmp_path):
        from services.calendar_service import CalendarService
        mock_settings.db_path = str(tmp_path / "cal.db")
        mock_settings.fernet_key = ""
        svc = CalendarService(mock_settings)
        assert svc._encrypt("test") == "test"
        assert svc._decrypt("test") == "test"
