# Setting Up Ollama with AI Companion

This guide will help you set up and use [Ollama](https://ollama.ai/) as the LLM provider for your AI Companion application.

## What is Ollama?

Ollama is an open-source tool that lets you run large language models locally on your machine. It provides a way to run LLMs like Llama, Mistral, Phi, and others through an OpenAI-compatible API interface.

## Installation

1. Download and install Ollama from [ollama.ai](https://ollama.ai/).
2. Once installed, Ollama runs as a service on your machine with an API endpoint at `http://localhost:11434`.

### System Requirements

Ollama can run on various machines, but for a better experience:
- At least 8GB RAM
- A modern CPU (for basic models)
- A dedicated GPU with at least 8GB VRAM (for larger models)

## Configuration

To use Ollama with AI Companion, update your `.env` file with the following settings:

```
# LLM Provider
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434/v1
OLLAMA_MODEL_NAME=phi4  # or another model you've pulled
```

## Available Models

To see all available models that you can use with Ollama:

```bash
ollama list
```

To download a new model:

```bash
ollama pull phi4
# or
ollama pull llama3
```

Some recommended models for AI Companion:
- `phi4` - Microsoft's Phi-4 model (4B parameters)
- `llama3` - Meta's Llama 3 (8B parameters)
- `mistral` - Mistral AI's model
- `gemma` - Google's Gemma model

## Limitations

- Ollama integration is for **LLM inference only**. It doesn't support Speech-to-Text (STT) or Text-to-Speech (TTS) functionalities.
- You'll need to continue using OpenAI, Groq, or ElevenLabs for STT and TTS features.
- Performance will vary based on your hardware, with larger models requiring more resources.
- The OpenAI compatibility layer in Ollama may have some differences compared to the actual OpenAI API.

## Troubleshooting

- **Model Loading Issues**: If a model fails to load, check if you have enough RAM/VRAM.
- **Slow Response Times**: Try using a smaller model or ensure no other resource-intensive applications are running.
- **API Connection Errors**: Make sure Ollama is running (`ollama serve` command if it stopped).
- **Model Not Found**: Run `ollama pull MODEL_NAME` to download the model first.

## Resources

- [Ollama Documentation](https://github.com/ollama/ollama/blob/main/README.md)
- [Ollama Model Library](https://ollama.ai/library)
- [Ollama GitHub Repository](https://github.com/ollama/ollama) 