# Ava WhatsApp Agent Extended

![License](https://img.shields.io/badge/license-MIT-blue.svg)

> **Honorable Mention**: This project is based on [Ava WhatsApp Agent Course](https://github.com/neural-maze/ava-whatsapp-agent-course) by Neural Maze. We've extended it with additional features like multi-provider support for image generation and analysis.

Ava is a versatile AI companion agent that can interact through chat, generate images, and convert speech to text and back. This project is built on a flexible architecture that supports multiple AI providers including OpenAI, Groq, Ollama, Together AI, and ElevenLabs.

## Features

- 💬 **Natural Conversation**: Have natural, context-aware conversations with your AI companion
- 🖼️ **Image Generation**: Generate images based on your descriptions, with support for Together AI or OpenAI DALL-E
- 🔍 **Image Analysis**: Analyze images with detailed descriptions using Groq or OpenAI
- 🗣️ **Voice Interaction**: Talk to your AI with text-to-speech (TTS) and speech-to-text (STT)
- 🧠 **Memory System**: Both short-term and long-term memory with vector database support
- 🔄 **Multi-Provider Support**: Switch between different LLM providers (OpenAI, Groq, Ollama)
- 📱 **WhatsApp Integration**: Chat with your AI companion directly through WhatsApp
- 💻 **Web Interface**: Interact through a browser-based Chainlit interface

## Architecture Overview

Ava is designed with a modular architecture that allows for flexible configuration and deployment:

![Architecture Overview](img/project_overview_diagram.gif)

### System Components:

1. **User Interfaces**:
   - WhatsApp for mobile messaging
   - Chainlit for web-based interaction

2. **Core Processing**:
   - LangGraph-powered workflow engine
   - Context injection for personalized responses
   - Memory management system

3. **AI Services**:
   - Text Generation: OpenAI, Groq, or Ollama
   - Image Generation: Together AI or OpenAI DALL-E
   - Image Analysis: Groq Llama or OpenAI GPT-4 Vision
   - Speech Processing: OpenAI or Groq for STT, OpenAI or ElevenLabs for TTS

4. **Storage**:
   - Vector Database (Weaviate or Qdrant) for long-term memory
   - Session-based short-term memory

## Supported Providers

- **LLM**: OpenAI, Groq, Ollama
- **Speech-to-Text**: OpenAI, Groq
- **Text-to-Speech**: OpenAI, ElevenLabs
- **Image-to-Text**: OpenAI, Groq
- **Text-to-Image**: OpenAI (DALL-E), Together AI

## Getting Started

See [GETTING_STARTED.md](docs/GETTING_STARTED.md) for detailed installation and configuration instructions.

### Quick Start

1. Clone this repository
2. Copy `.env.example` to `.env` and add your API keys
3. Choose your vector database (Qdrant or Weaviate)
4. Run the application with Docker Compose:

```bash
# For Qdrant
make ava-run-qdrant

# For Weaviate
make ava-run-weaviate
```

## Deployment Options

- **Local**: Run on your machine using Docker
- **Cloud**: Deploy to Google Cloud Run
- **Self-hosted Ollama**: Deploy Ollama models on vast.ai

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgements

This project is an extension of the [Ava WhatsApp Agent Course](https://github.com/neural-maze/ava-whatsapp-agent-course) by Neural Maze, a comprehensive course that teaches how to build a WhatsApp agent from scratch. We've built upon their excellent foundation to add multi-provider support and extended capabilities. 