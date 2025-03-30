from pydantic_settings import BaseSettings, SettingsConfigDict
from enum import Enum


class LLMProvider(str, Enum):
    GROQ = "groq"
    OPENAI = "openai"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore", env_file_encoding="utf-8")

    GROQ_API_KEY: str
    OPENAI_API_KEY: str
    LLM_PROVIDER: LLMProvider = LLMProvider.GROQ

    ELEVENLABS_API_KEY: str
    ELEVENLABS_VOICE_ID: str
    TOGETHER_API_KEY: str

    QDRANT_API_KEY: str | None
    QDRANT_URL: str
    QDRANT_PORT: str = "6333"
    QDRANT_HOST: str | None = None

    @property
    def TEXT_MODEL_NAME(self) -> str:
        """Get the appropriate text model name based on the provider."""
        if self.LLM_PROVIDER == LLMProvider.GROQ:
            return "llama-3.3-70b-versatile"
        else:  # OpenAI
            return "gpt-4o-2024-08-06"

    @property
    def SMALL_TEXT_MODEL_NAME(self) -> str:
        """Get the appropriate small text model name based on the provider."""
        if self.LLM_PROVIDER == LLMProvider.GROQ:
            return "gemma2-9b-it"
        else:  # OpenAI
            return "gpt-4o-mini-2024-07-18"

    STT_MODEL_NAME: str = "whisper-large-v3-turbo"
    TTS_MODEL_NAME: str = "eleven_flash_v2_5"
    TTI_MODEL_NAME: str = "black-forest-labs/FLUX.1-schnell-Free"
    ITT_MODEL_NAME: str = "llama-3.2-90b-vision-preview"

    MEMORY_TOP_K: int = 3
    ROUTER_MESSAGES_TO_ANALYZE: int = 3
    TOTAL_MESSAGES_SUMMARY_TRIGGER: int = 20
    TOTAL_MESSAGES_AFTER_SUMMARY: int = 5

    SHORT_TERM_MEMORY_DB_PATH: str = "/app/data/memory.db"


settings = Settings()
