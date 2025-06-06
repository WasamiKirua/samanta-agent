import re

from langchain_core.output_parsers import StrOutputParser
from langchain_groq import ChatGroq
from langchain_ollama import ChatOllama
from langchain_openai import ChatOpenAI

from ai_companion.modules.image.image_to_text import ImageToText
from ai_companion.modules.image.text_to_image import TextToImage
from ai_companion.modules.speech import TextToSpeech
from ai_companion.settings import settings, LLMProvider


def get_chat_model(temperature: float = 0.7):
    if settings.LLM_PROVIDER == LLMProvider.GROQ:
        return ChatGroq(
            api_key=settings.GROQ_API_KEY,
            model_name=settings.TEXT_MODEL_NAME,
            temperature=temperature,
        )
    elif settings.LLM_PROVIDER == LLMProvider.OLLAMA:
        return ChatOllama(
            model=settings.TEXT_MODEL_NAME,
            base_url=settings.OLLAMA_BASE_URL,
            temperature=temperature,
            timeout=60,
            max_retries=2,
            streaming=False,
        )
    else:  # OpenAI
        return ChatOpenAI(
            api_key=settings.OPENAI_API_KEY,
            model_name=settings.TEXT_MODEL_NAME,
            temperature=temperature,
        )


def get_text_to_speech_module():
    return TextToSpeech()


def get_text_to_image_module():
    return TextToImage()


def get_image_to_text_module():
    return ImageToText()


def remove_asterisk_content(text: str) -> str:
    """Remove content between asterisks from the text."""
    return re.sub(r"\*.*?\*", "", text).strip()


class AsteriskRemovalParser(StrOutputParser):
    def parse(self, text):
        return remove_asterisk_content(super().parse(text))
