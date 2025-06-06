import logging
import os
from io import BytesIO
from typing import Dict
import time
from collections import OrderedDict

import httpx
from fastapi import APIRouter, Request, Response
from langchain_core.messages import HumanMessage
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver

from ai_companion.graph import graph_builder
from ai_companion.modules.image import ImageToText
from ai_companion.modules.speech import SpeechToText, TextToSpeech
from ai_companion.settings import settings

logger = logging.getLogger(__name__)

# Global module instances
speech_to_text = SpeechToText()
text_to_speech = TextToSpeech()
image_to_text = ImageToText()

# Router for WhatsApp respo
whatsapp_router = APIRouter()

# WhatsApp API credentials
WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN")
WHATSAPP_PHONE_NUMBER_ID = os.getenv("WHATSAPP_PHONE_NUMBER_ID")

# Simple LRU cache for message deduplication (Avoid duplicate messages being processed)
class LRUCache:
    def __init__(self, capacity: int = 100):
        self.cache = OrderedDict()
        self.capacity = capacity
        
    def get(self, key):
        if key not in self.cache:
            return None
        # Move the key to the end to show that it was recently used
        self.cache.move_to_end(key)
        return self.cache[key]
        
    def put(self, key, value):
        if key in self.cache:
            # Move the key to the end to show that it was recently used
            self.cache.move_to_end(key)
        else:
            # Remove the first item if we're over capacity
            if len(self.cache) >= self.capacity:
                self.cache.popitem(last=False)
        self.cache[key] = value
        
# Initialize the message deduplication cache (Avoid duplicate messages being processed)
processed_messages = LRUCache(100)

@whatsapp_router.api_route("/whatsapp_response", methods=["GET", "POST"])
async def whatsapp_handler(request: Request) -> Response:
    """Handles incoming messages and status updates from the WhatsApp Cloud API."""

    if request.method == "GET":
        params = request.query_params
        if params.get("hub.verify_token") == os.getenv("WHATSAPP_VERIFY_TOKEN"):
            return Response(content=params.get("hub.challenge"), status_code=200)
        return Response(content="Verification token mismatch", status_code=403)

    try:
        data = await request.json()
        change_value = data["entry"][0]["changes"][0]["value"]
        if "messages" in change_value:
            message = change_value["messages"][0]
            
            # Extract message ID for deduplication (Avoid duplicate messages being processed)
            message_id = message.get("id")
            
            # Check if this message has already been processed (Avoid duplicate messages being processed)
            if message_id and processed_messages.get(message_id):
                logger.info(f"Ignoring duplicate message with ID: {message_id}")
                return Response(content="Duplicate message", status_code=200)
            
            # Mark this message as processed (Avoid duplicate messages being processed)
            if message_id:
                processed_messages.put(message_id, time.time())
            
            from_number = message["from"]
            session_id = from_number

            # Get user message and handle different message types
            content = ""
            if message["type"] == "audio":
                content = await process_audio_message(message)
            elif message["type"] == "image":
                # Get image caption if any
                content = message.get("image", {}).get("caption", "")
                # Download and analyze image
                image_bytes = await download_media(message["image"]["id"])
                try:
                    description = await image_to_text.analyze_image(
                        image_bytes,
                        "Please describe what you see in this image in the context of our conversation.",
                    )
                    content += f"\n[Image Analysis: {description}]"
                except Exception as e:
                    logger.warning(f"Failed to analyze image: {e}")
            else:
                content = message["text"]["body"]

            # Process message through the graph agent
            async with AsyncSqliteSaver.from_conn_string(settings.SHORT_TERM_MEMORY_DB_PATH) as short_term_memory:
                graph = graph_builder.compile(checkpointer=short_term_memory)
                await graph.ainvoke(
                    {"messages": [HumanMessage(content=content)]},
                    {"configurable": {"thread_id": session_id}},
                )

                # Get the workflow type and response from the state
                output_state = await graph.aget_state(config={"configurable": {"thread_id": session_id}})

            workflow = output_state.values.get("workflow", "conversation")
            response_message = output_state.values["messages"][-1].content

            # Handle different response types based on workflow
            if workflow == "audio":
                audio_buffer = output_state.values["audio_buffer"]
                success = await send_response(from_number, response_message, "audio", audio_buffer)
            elif workflow == "image":
                image_path = output_state.values["image_path"]
                with open(image_path, "rb") as f:
                    image_data = f.read()
                success = await send_response(from_number, response_message, "image", image_data)
            else:
                success = await send_response(from_number, response_message, "text")

            if not success:
                return Response(content="Failed to send message", status_code=500)

            return Response(content="Message processed", status_code=200)

        elif "statuses" in change_value:
            return Response(content="Status update received", status_code=200)

        else:
            return Response(content="Unknown event type", status_code=400)

    except Exception as e:
        logger.error(f"Error processing message: {e}", exc_info=True)
        return Response(content="Internal server error", status_code=500)


async def download_media(media_id: str) -> bytes:
    """Download media from WhatsApp."""
    media_metadata_url = f"https://graph.facebook.com/v22.0/{media_id}"
    headers = {"Authorization": f"Bearer {WHATSAPP_TOKEN}"}

    async with httpx.AsyncClient() as client:
        metadata_response = await client.get(media_metadata_url, headers=headers)
        metadata_response.raise_for_status()
        metadata = metadata_response.json()
        download_url = metadata.get("url")

        media_response = await client.get(download_url, headers=headers)
        media_response.raise_for_status()
        return media_response.content


async def process_audio_message(message: Dict) -> str:
    """Download and transcribe audio message."""
    try:
        audio_id = message["audio"]["id"]
        media_metadata_url = f"https://graph.facebook.com/v22.0/{audio_id}"
        headers = {"Authorization": f"Bearer {WHATSAPP_TOKEN}"}

        async with httpx.AsyncClient() as client:
            metadata_response = await client.get(media_metadata_url, headers=headers)
            metadata_response.raise_for_status()
            metadata = metadata_response.json()
            download_url = metadata.get("url")
            
            if not download_url:
                logger.error(f"Failed to get download URL for audio ID: {audio_id}")
                return "Sorry, I couldn't process your audio message. Please try again or send a text message instead."

        # Download the audio file
        async with httpx.AsyncClient() as client:
            audio_response = await client.get(download_url, headers=headers)
            audio_response.raise_for_status()
            
            # Log content type and size for debugging
            content_type = audio_response.headers.get("content-type", "unknown")
            content_length = audio_response.headers.get("content-length", "unknown")
            logger.info(f"Audio content type: {content_type}, size: {content_length} bytes")
            
            if not audio_response.content:
                logger.error("Downloaded audio content is empty")
                return "Sorry, I couldn't process your audio message. The audio file appears to be empty."

        # Prepare for transcription
        audio_buffer = BytesIO(audio_response.content)
        audio_buffer.seek(0)
        audio_data = audio_buffer.read()
        
        # Log audio data size
        logger.info(f"Audio data size: {len(audio_data)} bytes")
        
        if len(audio_data) < 100:  # Arbitrary small size threshold
            logger.error(f"Audio data too small: {len(audio_data)} bytes")
            return "Sorry, I couldn't process your audio message. The audio file appears to be too small or corrupted."

        return await speech_to_text.transcribe(audio_data)
    except Exception as e:
        logger.error(f"Error processing audio message: {str(e)}", exc_info=True)
        return "Sorry, I couldn't process your audio message. Please try again or send a text message instead."


async def send_response(
    from_number: str,
    response_text: str,
    message_type: str = "text",
    media_content: bytes = None,
) -> bool:
    """Send response to user via WhatsApp API."""
    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json",
    }

    if message_type in ["audio", "image"]:
        try:
            mime_type = "audio/mpeg" if message_type == "audio" else "image/png"
            media_buffer = BytesIO(media_content)
            media_id = await upload_media(media_buffer, mime_type)
            json_data = {
                "messaging_product": "whatsapp",
                "to": from_number,
                "type": message_type,
                message_type: {"id": media_id},
            }

            # Add caption for images
            if message_type == "image":
                json_data["image"]["caption"] = response_text
        except Exception as e:
            logger.error(f"Media upload failed, falling back to text: {e}")
            message_type = "text"

    if message_type == "text":
        json_data = {
            "messaging_product": "whatsapp",
            "to": from_number,
            "type": "text",
            "text": {"body": response_text},
        }

    print(headers)
    print(json_data)

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"https://graph.facebook.com/v22.0/{WHATSAPP_PHONE_NUMBER_ID}/messages",
            headers=headers,
            json=json_data,
        )

    return response.status_code == 200


async def upload_media(media_content: BytesIO, mime_type: str) -> str:
    """Upload media to WhatsApp servers."""
    headers = {"Authorization": f"Bearer {WHATSAPP_TOKEN}"}
    files = {"file": ("response.mp3", media_content, mime_type)}
    data = {"messaging_product": "whatsapp", "type": mime_type}

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"https://graph.facebook.com/v22.0/{WHATSAPP_PHONE_NUMBER_ID}/media",
            headers=headers,
            files=files,
            data=data,
        )
        result = response.json()

    if "id" not in result:
        raise Exception("Failed to upload media")
    return result["id"]
