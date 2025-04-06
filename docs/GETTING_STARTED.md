# Getting Started with Ava WhatsApp Agent Extended

This guide will walk you through the setup process for Ava, including configuration, deployment options, and usage instructions.

> **Note**: This project extends the original [Ava WhatsApp Agent Course](https://github.com/neural-maze/ava-whatsapp-agent-course) by Neural Maze with support for multiple AI providers and enhanced capabilities.

## Prerequisites

- Docker and Docker Compose installed
- Python 3.12 or higher (if running without Docker)
- API keys for the services you want to use

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/ava-whatsapp-agent-extended.git
cd ava-whatsapp-agent-extended
```

### 2. Configure Environment Variables

Copy the example environment file and add your API keys:

```bash
cp .env.example .env
```

Edit the `.env` file and add your API keys for the services you plan to use:

#### Required API Keys

| Provider | API Key | Required For |
|----------|---------|--------------|
| Groq | `GROQ_API_KEY` | LLM, Image-to-Text, Speech-to-Text (if using Groq) |
| OpenAI | `OPENAI_API_KEY` | LLM, Image-to-Text, Text-to-Image, Speech-to-Text (if using OpenAI) |
| Together | `TOGETHER_API_KEY` | Text-to-Image (if using Together) |
| ElevenLabs | `ELEVENLABS_API_KEY` | Text-to-Speech (if using ElevenLabs) |

#### Provider Configuration

You can choose which providers to use for different functionalities:

```
# LLM Provider (for text generation)
LLM_PROVIDER=groq  # Options: "groq", "openai", "ollama"

# Image-to-Text provider
ITT_PROVIDER="groq"  # Options: "groq" or "openai"

# Text-to-Image provider
TTI_PROVIDER="together"  # Options: "together" or "openai"

# Speech-to-Text provider
STT_PROVIDER="openai"  # Options: "groq" or "openai"

# Text-to-Speech provider
TTS_PROVIDER="openai"  # Options: "elevenlabs" or "openai"
```

#### Vector Database Selection

Choose your preferred vector database for long-term memory:

```
# Vector Database provider
VECTOR_DB_PROVIDER="qdrant"  # Options: "qdrant" or "weaviate"
```

### 3. Running with Docker

#### Run with Qdrant

```bash
make ava-build-qdrant
make ava-run-qdrant
```

#### Run with Weaviate

```bash
make ava-build-weaviate
make ava-run-weaviate
```

### 4. Accessing the Interfaces

- **Chainlit Web Interface**: http://localhost:8000
- **WhatsApp Webhook**: http://localhost:8081/whatsapp_response

## Ollama Integration

Ava supports using Ollama as an LLM provider. This allows you to run open-source models locally or on a self-hosted server.

### Local Ollama Setup

1. Install Ollama from [ollama.ai](https://ollama.ai/)
2. Pull your desired model:
   ```bash
   ollama pull phi4
   ```
3. Configure `.env` to use Ollama:
   ```
   LLM_PROVIDER="ollama"
   OLLAMA_BASE_URL="http://host.docker.internal:11434"
   OLLAMA_MODEL_NAME="phi4"
   ```

### Deploying Ollama on vast.ai

For more powerful inference capabilities, you can deploy Ollama on vast.ai:

1. Set up your vast.ai API key in `.env`:
   ```
   VASTAI_KEY="your-vast-ai-key"
   HF_TOKEN="your-huggingface-token"  # Optional, for pulling HF models
   NUM_GPUS=1
   DISK_SIZE=30
   MODEL_NAME_OLLAMA="phi4"
   INSTANCE_TAG="ava"
   ```

2. Use the vastai-deployment tools to deploy:
   ```bash
   cd vastai-deployment
   python ollama-vastai-provision.py
   ```

3. Follow the interactive deployment process:
   - The script will search for available GPU instances on vast.ai
   - You'll see a list of available instances with pricing information
   - Select the instance number you want to use
   - The script will create the instance and set up Ollama
   - Wait for deployment to complete (usually 3-5 minutes)
   - The script will automatically pull your specified model
   - Connection details will be displayed when finished

4. Update your `.env` with the Ollama endpoint URL displayed at the end:
   ```
   OLLAMA_BASE_URL="http://[VAST_AI_IP]:[PORT]"
   ```

## WhatsApp Integration

To integrate with WhatsApp via Meta's WhatsApp Business API:

1. Register for a Meta Developer account and create a WhatsApp Business App
2. Configure your webhook URL (your deployed WhatsApp service endpoint)
3. Add the WhatsApp credentials to your `.env`:
   ```
   WHATSAPP_PHONE_NUMBER_ID="your-phone-number-id"
   WHATSAPP_TOKEN="your-token"
   WHATSAPP_VERIFY_TOKEN="your-verify-token"
   ```

## Cloud Deployment

### Google Cloud Run

The repository includes a `cloudbuild.yaml` file for easy deployment to Google Cloud Run:

1. Set up Google Cloud SDK
2. Configure Google Cloud Build to use your repository
3. Set up your secrets in Google Cloud Secret Manager
4. Deploy with:
   ```bash
   gcloud builds submit
   ```

## Memory System

Ava uses a dual-memory system:

- **Short-term memory**: Maintained in the conversation session
- **Long-term memory**: Stored in a vector database (Qdrant or Weaviate)

The memory system automatically extracts important information from conversations and stores it for future reference.

## Working with Images

### Generating Images

Ava can generate images in two ways:

1. **Direct prompt**: Provide a description to generate an image
2. **Scenario generation**: Generate a narrative and visual scene based on conversation context

Images can be generated using:
- Together AI (default): Works well for creative images
- OpenAI (DALL-E): High-quality photorealistic images

### Analyzing Images

Ava can analyze images sent by the user and describe their content using:
- Groq: Fast analysis with the Llama model
- OpenAI: Detailed analysis with GPT-4 Vision

## Troubleshooting

### Common Issues

- **Container connectivity issues**: Ensure all container ports are properly exposed
- **Memory errors**: Check Docker memory allocation if using large models
- **API rate limits**: You might encounter rate limits with free tier API keys

### Logs

View logs for running containers:

```bash
# Chainlit interface logs
docker logs ava-whatsapp-agent-extended-chainlit-1

# WhatsApp interface logs
docker logs ava-whatsapp-agent-extended-whatsapp-1
```

## Credits

This project is an extension of the [Ava WhatsApp Agent Course](https://github.com/neural-maze/ava-whatsapp-agent-course) by Neural Maze. 