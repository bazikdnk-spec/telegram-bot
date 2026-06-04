from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    telegram_token: str = Field(..., alias="TELEGRAM_TOKEN")
    groq_api_key: str = Field(..., alias="GROQ_API_KEY")

    db_path: str = "bot.db"
    default_model: str = "llama-3.1-8b-instant"
    complex_model: str = "llama-3.3-70b-versatile"
    vision_model: str = "meta-llama/llama-4-scout-17b-16e-instruct"
    audio_model: str = "whisper-large-v3"

    # Rate limits
    rate_limit_per_user: int = 10
    rate_limit_per_chat: int = 50
    rate_limit_global_rpm: int = 30

    # Redis
    redis_host: str = Field("localhost", alias="REDIS_HOST")
    redis_port: int = Field(6379, alias="REDIS_PORT")

    # Postgres
    postgres_dsn: str = Field("postgresql://postgres:postgres@localhost:5432/botdb", alias="POSTGRES_DSN")

    # Ollama
    ollama_host: str = Field("http://localhost:11434", alias="OLLAMA_HOST")
    ollama_default_model: str = Field("llama3.2:3b", alias="OLLAMA_MODEL")

    # Search API (Tavily or Serper)
    search_api_key: str = Field("", alias="SEARCH_API_KEY")
    search_provider: str = Field("tavily", alias="SEARCH_PROVIDER")

    # SiliconFlow (free FLUX image generation, no card needed — cloud.siliconflow.cn)
    siliconflow_api_key: str = Field("", alias="SILICONFLOW_API_KEY")

    # Google Calendar
    google_credentials_file: str = Field("google_credentials.json", alias="GOOGLE_CREDENTIALS_FILE")
    fernet_key: str = Field("", alias="FERNET_KEY")

    # Webhook
    webhook_url: str = Field("", alias="WEBHOOK_URL")
    webhook_port: int = Field(8443, alias="WEBHOOK_PORT")
    webhook_path: str = Field("/webhook", alias="WEBHOOK_PATH")

    # Logging
    log_file: str = "bot.log"
    log_level: str = "INFO"

    # MCP
    mcp_bearer_token: str = Field("secret-mcp-token", alias="MCP_BEARER_TOKEN")
    mcp_http_port: int = Field(8080, alias="MCP_HTTP_PORT")

    # Context window limit (tokens)
    context_max_tokens: int = 6000

    # Admin user IDs (comma-separated)
    admin_ids: str = Field("", alias="ADMIN_IDS")

    def get_admin_ids(self) -> list[int]:
        if not self.admin_ids:
            return []
        return [int(x.strip()) for x in self.admin_ids.split(",") if x.strip()]

    model_config = SettingsConfigDict(
        env_file=(".env", ".env.local"),
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
    )


try:
    settings = Settings()
except Exception as e:
    import sys
    print(f"CRITICAL CONFIG ERROR: Не удалось загрузить конфигурацию. {e}")
    sys.exit(1)
