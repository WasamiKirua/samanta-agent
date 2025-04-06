# Ollama Deployment on vast.ai

This tool automates the deployment of Ollama instances on vast.ai cloud GPU providers for use with Ava WhatsApp Agent.

> **Note**: This deployment tool is part of the [Ava WhatsApp Agent Extended](https://github.com/yourusername/ava-whatsapp-agent-extended) project, which extends the original [Ava WhatsApp Agent Course](https://github.com/neural-maze/ava-whatsapp-agent-course).

## Features

- 🔍 Automatic search for cost-effective GPU instances
- 🚀 Automated setup and model loading
- 🔄 Easy integration with Ava
- 💰 Cost-effective AI model hosting

## Requirements

- A vast.ai account and API key
- Python 3.7+
- Required Python packages (install with `pip install -r requirements.txt`)

## Usage

1. Configure your `.env` file in the root directory:

```
VASTAI_KEY="your-vast-ai-key"
HF_TOKEN="your-huggingface-token" # Optional for HF models
NUM_GPUS=1
DISK_SIZE=30
MODEL_NAME_OLLAMA="phi4"
INSTANCE_TAG="ava"
```

2. Run the deployment script:

```bash
# Install dependencies
pip install -r requirements.txt

# Run the deployment
python ollama-vastai-provision.py
```

3. Follow the interactive steps:
   - The script will search for available instances on vast.ai
   - You'll see a list of available GPU instances with pricing
   - Select the instance number you want to use
   - The script will create the instance and deploy Ollama
   - Wait for deployment to complete (usually 3-5 minutes)
   - The script will pull your specified model automatically

4. Update your Ava `.env` file with the Ollama URL provided in the output.

## How It Works

The script:

1. Searches for available GPU instances on vast.ai that match your requirements
2. Presents available options and lets you select the best instance for your needs
3. Sets up Ollama and configures it to accept remote connections
4. Pulls and loads your specified model
5. Outputs connection details for Ava integration

## Cost Considerations

- vast.ai charges by the hour for GPU instances
- Costs vary depending on GPU type, from $0.10/hr to $1.5+/hr
- Remember to destroy instances when not in use to avoid ongoing charges

## Destroying Instances

To destroy your instance and stop billing:

```bash
# Using vast.ai CLI
vastai destroy <instance_id>

# Or via web interface
# Visit https://console.vast.ai/
```

## Troubleshooting

If the deployment fails:

1. Check your vast.ai account for available funds
2. Verify your API key is correct
3. Try different GPU requirements in your .env file
4. Check the vast.ai console for error messages 