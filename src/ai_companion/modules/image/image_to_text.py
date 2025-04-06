import base64
import logging
import os
from typing import Optional, Union

from ai_companion.core.exceptions import ImageToTextError
from ai_companion.settings import settings, ITTProvider
from groq import Groq
from openai import OpenAI


class ImageToText:
    """A class to handle image-to-text conversion using Groq or OpenAI vision capabilities."""

    REQUIRED_ENV_VARS = ["GROQ_API_KEY", "OPENAI_API_KEY"]

    def __init__(self):
        """Initialize the ImageToText class and validate environment variables."""
        self._validate_env_vars()
        self._client: Optional[Union[Groq, OpenAI]] = None
        self.logger = logging.getLogger(__name__)

    def _validate_env_vars(self) -> None:
        """Validate that all required environment variables are set."""
        missing_vars = [var for var in self.REQUIRED_ENV_VARS if not os.getenv(var)]
        if missing_vars:
            raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")

    @property
    def client(self) -> Union[Groq, OpenAI]:
        """Get or create client instance using singleton pattern based on provider."""
        if self._client is None:
            if settings.ITT_PROVIDER == ITTProvider.GROQ:
                self._client = Groq(api_key=settings.GROQ_API_KEY)
            else:  # OpenAI
                self._client = OpenAI(api_key=settings.OPENAI_API_KEY)
        return self._client

    async def analyze_image(self, image_data: Union[str, bytes], prompt: str = "") -> str:
        """Analyze an image using Groq or OpenAI vision capabilities.

        Args:
            image_data: Either a file path (str) or binary image data (bytes)
            prompt: Optional prompt to guide the image analysis

        Returns:
            str: Description or analysis of the image

        Raises:
            ValueError: If the image data is empty or invalid
            ImageToTextError: If the image analysis fails
        """
        try:
            # Handle file path
            if isinstance(image_data, str):
                if not os.path.exists(image_data):
                    raise ValueError(f"Image file not found: {image_data}")
                with open(image_data, "rb") as f:
                    image_bytes = f.read()
            else:
                image_bytes = image_data

            if not image_bytes:
                raise ValueError("Image data cannot be empty")

            # Convert image to base64
            base64_image = base64.b64encode(image_bytes).decode("utf-8")

            # Default prompt if none provided
            if not prompt:
                prompt = "Please describe what you see in this image in detail."

            # Create the messages for the vision API
            messages = [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"},
                        },
                    ],
                }
            ]

            # Make the API call based on provider
            if settings.ITT_PROVIDER == ITTProvider.GROQ:
                response = self.client.chat.completions.create(
                    model=settings.ITT_GROQ_MODEL_NAME,
                    messages=messages,
                    max_tokens=1000,
                )
            else:  # OpenAI
                response = self.client.chat.completions.create(
                    model=settings.ITT_OPENAI_MODEL_NAME,
                    messages=messages,
                    max_tokens=1000,
                )

            if not response.choices:
                raise ImageToTextError("No response received from the vision model")

            description = response.choices[0].message.content
            self.logger.info(f"Generated image description: {description}")

            return description

        except Exception as e:
            raise ImageToTextError(f"Failed to analyze image: {str(e)}") from e
