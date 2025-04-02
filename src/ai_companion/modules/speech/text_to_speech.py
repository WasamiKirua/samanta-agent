import os
from typing import Optional, Union
from pathlib import Path

from ai_companion.core.exceptions import TextToSpeechError
from ai_companion.settings import settings, TTSProvider
from elevenlabs import ElevenLabs, Voice, VoiceSettings
from openai import OpenAI


class TextToSpeech:
    """A class to handle text-to-speech conversion using ElevenLabs or OpenAI."""

    # Required environment variables
    REQUIRED_ENV_VARS = ["TTS_PROVIDER"]

    def __init__(self):
        """Initialize the TextToSpeech class and validate environment variables."""
        self._validate_env_vars()
        self._client: Optional[Union[ElevenLabs, OpenAI]] = None

    def _validate_env_vars(self) -> None:
        """Validate that all required environment variables are set."""
        missing_vars = [var for var in self.REQUIRED_ENV_VARS if not os.getenv(var)]
        if missing_vars:
            raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")

    @property
    def client(self) -> Union[ElevenLabs, OpenAI]:
        """Get or create client instance using singleton pattern."""
        if self._client is None:
            if settings.TTS_PROVIDER == TTSProvider.ELEVENLABS:
                self._client = ElevenLabs(api_key=settings.ELEVENLABS_API_KEY)
            else:  # OpenAI
                self._client = OpenAI(api_key=settings.OPENAI_API_KEY)
        return self._client

    async def synthesize(self, text: str) -> bytes:
        """Convert text to speech using the selected provider.

        Args:
            text: Text to convert to speech

        Returns:
            bytes: Audio data

        Raises:
            ValueError: If the input text is empty or too long
            TextToSpeechError: If the text-to-speech conversion fails
        """
        if not text.strip():
            raise ValueError("Input text cannot be empty")

        if len(text) > 5000:  # ElevenLabs typical limit
            raise ValueError("Input text exceeds maximum length of 5000 characters")

        try:
            if settings.TTS_PROVIDER == TTSProvider.ELEVENLABS:
                audio_generator = self.client.generate(
                    text=text,
                    voice=Voice(
                        voice_id=settings.ELEVENLABS_VOICE_ID,
                        settings=VoiceSettings(stability=0.5, similarity_boost=0.5),
                    ),
                    model=settings.TTS_ELEVENLAB_MODEL_NAME,
                )
                # Convert generator to bytes
                audio_bytes = b"".join(audio_generator)
                if not audio_bytes:
                    raise TextToSpeechError("Generated audio is empty")
                return audio_bytes
            else:  # OpenAI
                response = self.client.audio.speech.create(
                    model=settings.TTS_OPENAI_MODEL_NAME,
                    voice=settings.OPENAI_VOICE_ID,
                    input=text
                )
                # OpenAI returns a file-like object that we can read directly
                return response.read()

        except Exception as e:
            raise TextToSpeechError(f"Text-to-speech conversion failed: {str(e)}") from e
