from io import BytesIO

import chainlit as cl
from langchain_core.messages import AIMessageChunk, HumanMessage
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver

from ai_companion.graph import graph_builder
from ai_companion.modules.image import ImageToText
from ai_companion.modules.speech import SpeechToText, TextToSpeech
from ai_companion.settings import settings

# Global module instances
speech_to_text = SpeechToText()
text_to_speech = TextToSpeech()
image_to_text = ImageToText()


@cl.on_chat_start
async def on_chat_start():
    """Initialize the chat session"""
    # thread_id = cl.user_session.get("id")
    cl.user_session.set("thread_id", 1)


@cl.on_message
async def on_message(message: cl.Message):
    """Handle text messages and images"""
    msg = cl.Message(content="")

    # Process any attached images
    content = message.content
    if message.elements:
        for elem in message.elements:
            if isinstance(elem, cl.Image):
                # Read image file content
                with open(elem.path, "rb") as f:
                    image_bytes = f.read()

                # Analyze image and add to message content
                try:
                    # Use global ImageToText instance
                    description = await image_to_text.analyze_image(
                        image_bytes,
                        "Please describe what you see in this image in the context of our conversation.",
                    )
                    content += f"\n[Image Analysis: {description}]"
                except Exception as e:
                    cl.logger.warning(f"Failed to analyze image: {e}")

    # Process through graph with enriched message content
    thread_id = cl.user_session.get("thread_id")

    async with cl.Step(type="run"):
        async with AsyncSqliteSaver.from_conn_string(settings.SHORT_TERM_MEMORY_DB_PATH) as short_term_memory:
            graph = graph_builder.compile(checkpointer=short_term_memory)
            async for chunk in graph.astream(
                {"messages": [HumanMessage(content=content)]},
                {"configurable": {"thread_id": thread_id}},
                stream_mode="messages",
            ):
                if chunk[1]["langgraph_node"] == "conversation_node" and isinstance(chunk[0], AIMessageChunk):
                    await msg.stream_token(chunk[0].content)

            output_state = await graph.aget_state(config={"configurable": {"thread_id": thread_id}})

    if output_state.values.get("workflow") == "audio":
        response = output_state.values["messages"][-1].content
        audio_buffer = output_state.values["audio_buffer"]
        output_audio_el = cl.Audio(
            name="Audio",
            auto_play=True,
            mime="audio/mpeg3",
            content=audio_buffer,
        )
        await cl.Message(content=response, elements=[output_audio_el]).send()
    elif output_state.values.get("workflow") == "image":
        response = output_state.values["messages"][-1].content
        image = cl.Image(path=output_state.values["image_path"], display="inline")
        await cl.Message(content=response, elements=[image]).send()
    else:
        await msg.send()


@cl.on_audio_chunk
async def on_audio_chunk(chunk: cl.AudioChunk):
    """Handle incoming audio chunks"""
    if chunk.isStart:
        buffer = BytesIO()
        # Store the original MIME type
        mime_type = chunk.mimeType
        # Get file extension from MIME type
        extension = mime_type.split('/')[1]
        
        # Set the buffer name with the correct extension
        buffer.name = f"input_audio.{extension}"
        
        cl.user_session.set("audio_buffer", buffer)
        cl.user_session.set("audio_mime_type", mime_type)
        cl.user_session.set("audio_extension", extension)
        print(f"Starting audio recording with MIME type: {mime_type}")
    
    cl.user_session.get("audio_buffer").write(chunk.data)


@cl.on_audio_end
async def on_audio_end(elements):
    """Handle end of audio recording"""
    audio_buffer = cl.user_session.get("audio_buffer")
    audio_mime_type = cl.user_session.get("audio_mime_type")
    audio_extension = cl.user_session.get("audio_extension")
    
    # Log the audio details for debugging
    print(f"Audio MIME type: {audio_mime_type}")
    print(f"Audio extension: {audio_extension}")
    
    audio_buffer.seek(0)
    audio_data = audio_buffer.read()
    
    # Log the audio file size for debugging
    print(f"Audio file size: {len(audio_data)} bytes")
    
    # Show user's audio message
    input_audio_el = cl.Audio(mime=audio_mime_type, content=audio_data)
    await cl.Message(author="You", content="", elements=[input_audio_el, *elements]).send()
    
    try:
        # Create a new BytesIO object with the correct filename for transcription
        # This helps the speech_to_text module identify the correct format
        transcription_buffer = BytesIO(audio_data)
        
        # Ensure we're using the correct file extension
        # OpenAI supports mp3, mp4, mpeg, mpga, m4a, wav, and webm
        transcription_buffer.name = f"audio.{audio_extension}"
        print(f"Created transcription buffer with name: {transcription_buffer.name}")
        
        # Use global SpeechToText instance - pass the buffer object directly to preserve filename
        transcription = await speech_to_text.transcribe(transcription_buffer)
        
        thread_id = cl.user_session.get("thread_id")
        
        async with AsyncSqliteSaver.from_conn_string(settings.SHORT_TERM_MEMORY_DB_PATH) as short_term_memory:
            graph = graph_builder.compile(checkpointer=short_term_memory)
            output_state = await graph.ainvoke(
                {"messages": [HumanMessage(content=transcription)]},
                {"configurable": {"thread_id": thread_id}},
            )
        
        # Use global TextToSpeech instance
        audio_buffer = await text_to_speech.synthesize(output_state["messages"][-1].content)
        
        # Send the response
        await cl.Message(
            author="Assistant",
            content=output_state["messages"][-1].content,
            elements=[cl.Audio(mime="audio/mpeg", content=audio_buffer)],
        ).send()
    except Exception as e:
        # Log the error for debugging
        print(f"Error processing audio: {str(e)}")
        # Send an error message to the user
        await cl.Message(
            author="Assistant",
            content=f"I'm sorry, I couldn't process your audio message. Error: {str(e)}",
        ).send()
