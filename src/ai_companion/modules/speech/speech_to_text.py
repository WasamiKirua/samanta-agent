import os
import tempfile
from typing import Optional, Union
from io import BytesIO

from ai_companion.core.exceptions import SpeechToTextError
from ai_companion.settings import settings, STTProvider
from groq import Groq
from openai import OpenAI


class SpeechToText:
    """A class to handle speech-to-text conversion using Groq's Whisper model or OpenAI"""

    # Required environment variables
    REQUIRED_ENV_VARS = ["STT_PROVIDER", "STT_LANGUAGE"]

    def __init__(self):
        """Initialize the SpeechToText class and validate environment variables."""
        self._validate_env_vars()
        self._client: Optional[Union[Groq, OpenAI]] = None

    def _validate_env_vars(self) -> None:
        """Validate that all required environment variables are set."""
        missing_vars = [var for var in self.REQUIRED_ENV_VARS if not os.getenv(var)]
        if missing_vars:
            raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")

    @property
    def client(self) -> Union[Groq, OpenAI]:
        """Get or create client instance using singleton pattern."""
        if self._client is None:
            if settings.STT_PROVIDER == STTProvider.GROQ:
                self._client = Groq(api_key=settings.GROQ_API_KEY)
            else:  # OpenAI
                self._client = OpenAI(api_key=settings.OPENAI_API_KEY)
        return self._client

    @property
    def stt_model(self) -> tuple[str, str]:
        """Get the appropriate STT model and language based on provider."""
        if settings.STT_PROVIDER == STTProvider.GROQ:
            return settings.STT_GROQ_MODEL_NAME, settings.STT_LANGUAGE
        else:  # OpenAI
            return settings.STT_OPENAI_MODEL_NAME, settings.STT_LANGUAGE

    async def transcribe(self, audio_data: Union[bytes, BytesIO]) -> str:
        """Convert speech to text using the selected provider's model.

        Args:
            audio_data: Binary audio data or BytesIO object

        Returns:
            str: Transcribed text

        Raises:
            ValueError: If the audio file is empty or invalid
            SpeechToTextError: If the transcription fails
        """
        if not audio_data:
            raise ValueError("Audio data cannot be empty")

        # Handle BytesIO objects from Chainlit
        if isinstance(audio_data, BytesIO):
            file_obj = audio_data
            # Make sure we're at the beginning of the buffer
            file_obj.seek(0)
            # Get raw bytes for writing to temp file
            raw_bytes = file_obj.getvalue()
            # Log filename
            if hasattr(file_obj, 'name'):
                print(f"Using provided BytesIO with name: {file_obj.name}")
        else:
            # Handle raw bytes from WhatsApp
            raw_bytes = audio_data
            file_obj = None
            
        try:
            # Create a temporary file with appropriate extension based on provider
            if settings.STT_PROVIDER == STTProvider.OPENAI:
                # OpenAI supports mp3, mp4, mpeg, mpga, m4a, wav, and webm
                suffix = ".ogg"  # Default for WhatsApp which sends ogg
            else:  # Groq
                # Groq supports more formats, including ogg
                suffix = ".ogg"
                
            with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as temp_file:
                temp_file.write(raw_bytes)
                temp_file_path = temp_file.name

            try:
                # Open the temporary file for the API request
                with open(temp_file_path, "rb") as audio_file:
                    model, language = self.stt_model
                    
                    # Log the file size for debugging
                    file_size = os.path.getsize(temp_file_path)
                    print(f"Audio file size: {file_size} bytes")
                    
                    # For OpenAI, we don't specify file_format as it's not supported
                    if settings.STT_PROVIDER == STTProvider.OPENAI:
                        if file_obj is not None:
                            # For Chainlit: use the BytesIO object directly with its filename
                            # Reset position to beginning of buffer
                            file_obj.seek(0)
                            print(f"Using file extension from BytesIO: {file_obj.name}")
                            
                            transcription = self.client.audio.transcriptions.create(
                                file=file_obj,
                                model=model,
                                language=language,
                                response_format="text"
                            )
                        else:
                            # For WhatsApp: create a new BytesIO with default name
                            whatsapp_file_obj = BytesIO(raw_bytes)
                            whatsapp_file_obj.name = "audio.ogg"  # Default for WhatsApp
                            print(f"Using default file extension for WhatsApp: {whatsapp_file_obj.name}")
                            
                            transcription = self.client.audio.transcriptions.create(
                                file=whatsapp_file_obj,
                                model=model,
                                language=language,
                                response_format="text"
                            )
                    else:  # Groq
                        transcription = self.client.audio.transcriptions.create(
                            file=audio_file,
                            model=model,
                            language=language,
                            response_format="text",
                        )

                if not transcription:
                    raise SpeechToTextError("Transcription result is empty")

                return transcription

            finally:
                # Clean up the temporary file
                os.unlink(temp_file_path)

        except Exception as e:
            raise SpeechToTextError(f"Speech-to-text conversion failed: {str(e)}") from e
