from pydantic_settings import BaseSettings, SettingsConfigDict
from enum import Enum


class LLMProvider(str, Enum):
    GROQ = "groq"
    OPENAI = "openai"
    OLLAMA = "ollama"

class VectorDBProvider(str, Enum):
    QDRANT = "qdrant"
    WEAVIATE = "weaviate"

class STTProvider(str, Enum):
    GROQ = "groq"
    OPENAI = "openai"

class TTSProvider(str, Enum):
    ELEVENLABS = "elevenlabs"
    OPENAI = "openai"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore", env_file_encoding="utf-8")

    GROQ_API_KEY: str
    OPENAI_API_KEY: str
    LLM_PROVIDER: LLMProvider = LLMProvider.GROQ

    STT_PROVIDER: STTProvider = STTProvider.GROQ
    STT_LANGUAGE: str = "en"
    STT_GROQ_MODEL_NAME: str = "whisper-large-v3-turbo"
    STT_OPENAI_MODEL_NAME: str = "gpt-4o-transcribe"


    TTS_PROVIDER: TTSProvider = TTSProvider.ELEVENLABS
    TTS_ELEVENLAB_MODEL_NAME: str = "eleven_flash_v2_5"
    TTS_OPENAI_MODEL_NAME: str = "gpt-4o-mini-tts"

    ELEVENLABS_API_KEY: str
    ELEVENLABS_VOICE_ID: str
    OPENAI_VOICE_ID: str
    TOGETHER_API_KEY: str

    # Vector Database Settings
    VECTOR_DB_PROVIDER: VectorDBProvider = VectorDBProvider.QDRANT
    
    # Qdrant Settings
    QDRANT_API_KEY: str | None
    QDRANT_URL: str
    QDRANT_PORT: str = "6333"
    QDRANT_HOST: str | None = None
    
    # Weaviate Settings
    WEAVIATE_HOST: str
    WEAVIATE_PORT: int

    # Ollama settings
    OLLAMA_BASE_URL: str
    OLLAMA_MODEL_NAME: str

    @property
    def TEXT_MODEL_NAME(self) -> str:
        """Get the appropriate text model name based on the provider."""
        if self.LLM_PROVIDER == LLMProvider.GROQ:
            return "llama-3.3-70b-versatile"
        elif self.LLM_PROVIDER == LLMProvider.OLLAMA:
            return self.OLLAMA_MODEL_NAME
        else:  # OpenAI
            return "gpt-4o-2024-08-06"
    
    @property
    def SMALL_TEXT_MODEL_NAME(self) -> str:
        """Get the appropriate small text model name based on the provider."""
        if self.LLM_PROVIDER == LLMProvider.GROQ:
            return "gemma2-9b-it"
        elif self.LLM_PROVIDER == LLMProvider.OLLAMA:
            return self.OLLAMA_MODEL_NAME
        else:  # OpenAI
            return "gpt-4o-mini-2024-07-18"

    @property
    def MEMORY_MODEL_NAME(self) -> str:
        """Get the model name for memory-related tasks (always fixed, not Ollama)."""
        if self.LLM_PROVIDER == LLMProvider.GROQ or (self.GROQ_API_KEY and not self.OPENAI_API_KEY):
            return "gemma2-9b-it"  # Fixed Groq model
        else:
            return "gpt-4o-mini"   # Fixed OpenAI model
            
    @property
    def IMAGE_MODEL_NAME(self) -> str:
        """Get the model name for image-related tasks (always fixed, not Ollama)."""
        if self.LLM_PROVIDER == LLMProvider.GROQ or (self.GROQ_API_KEY and not self.OPENAI_API_KEY):
            return "llama-3.1-8b-instant"  # Fixed Groq model
        else:
            return "gpt-4o-mini"   # Fixed OpenAI model

    TTI_MODEL_NAME: str = "black-forest-labs/FLUX.1-schnell-Free"
    ITT_MODEL_NAME: str = "llama-3.2-90b-vision-preview"

    MEMORY_TOP_K: int = 3
    ROUTER_MESSAGES_TO_ANALYZE: int = 3
    TOTAL_MESSAGES_SUMMARY_TRIGGER: int = 20
    TOTAL_MESSAGES_AFTER_SUMMARY: int = 5

    SHORT_TERM_MEMORY_DB_PATH: str = "/app/data/memory.db"


settings = Settings()
