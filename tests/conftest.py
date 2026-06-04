import pytest
from unittest.mock import AsyncMock, MagicMock
from config.settings import Settings


@pytest.fixture
def mock_settings():
    s = MagicMock(spec=Settings)
    s.telegram_token = "test:token"
    s.groq_api_key = "test_key"
    s.db_path = ":memory:"
    s.default_model = "llama-3.1-8b-instant"
    s.complex_model = "llama-3.3-70b-versatile"
    s.vision_model = "llama-3.2-11b-vision-preview"
    s.audio_model = "whisper-large-v3"
    s.rate_limit_per_user = 10
    s.rate_limit_per_chat = 50
    s.rate_limit_global_rpm = 30
    s.redis_host = "localhost"
    s.redis_port = 6379
    s.context_max_tokens = 6000
    s.search_api_key = ""
    s.search_provider = "tavily"
    s.replicate_api_key = ""
    s.ollama_host = "http://localhost:11434"
    s.ollama_default_model = "llama3.2:3b"
    s.fernet_key = ""
    s.google_credentials_file = "google_credentials.json"
    s.webhook_url = ""
    s.log_file = "test.log"
    s.log_level = "DEBUG"
    s.admin_ids = ""
    s.get_admin_ids = MagicMock(return_value=[])
    return s


@pytest.fixture
def mock_groq_service(mock_settings):
    from services.groq_service import GroqService
    svc = MagicMock(spec=GroqService)
    svc.settings = mock_settings

    async def fake_stream(user_id, text, model=None):
        yield "Тестовый ответ"

    svc.get_ai_stream_response = fake_stream
    svc.get_simple_response = AsyncMock(return_value="Простой ответ")
    svc.clear_history = MagicMock()
    svc.save_message = MagicMock()
    svc.get_user_history = MagicMock(return_value=[])
    svc.transcribe_audio = AsyncMock(return_value="Привет")
    return svc


@pytest.fixture
def mock_rate_limiter():
    from services.rate_limiter import InMemoryRateLimiter
    limiter = MagicMock(spec=InMemoryRateLimiter)
    limiter.check = AsyncMock(return_value=(True, ""))
    return limiter


@pytest.fixture
def mock_message():
    msg = MagicMock()
    msg.from_user.id = 12345
    msg.from_user.first_name = "Тест"
    msg.from_user.username = "testuser"
    msg.chat.id = 12345
    msg.text = "Привет, бот!"
    msg.answer = AsyncMock(return_value=MagicMock(edit_text=AsyncMock()))
    return msg
