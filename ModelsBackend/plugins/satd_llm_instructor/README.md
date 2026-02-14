# SATD LLM Detector Plugin

## Overview
This plugin uses Large Language Models (LLMs) via the `instructor` library to classify GitHub issues for Self-Admitted Technical Debt (SATD). It is designed to work with native API providers for ease of use and consistent configuration.

## Configuration
The plugin can be configured in `ModelsBackend/config.json`.

### Model Selection
You can use models from various providers by specifying the `model_name` in the format `<provider>/<model_name>`. For example:
- **Google**: `google/gemini-2.5-flash`
- **OpenAI**: `openai/gpt-5-nano`
- **Anthropic**: `anthropic/claude-3-haiku`

> **Note on Dependencies**: If you use a provider other than the three listed above (e.g., `groq`, `mistral`), you must manually install their specific Python SDK in your environment (e.g., `pip install groq`).

### Prompts
The classification logic is driven by `prompts.json`. You can customize the system and user messages to refine the LLM's understanding of technical debt.

## Environment Variables
Set these in `ModelsBackend/.env`:
- `GEMINI_API_KEY`: Required for Google models via AI Studio.
- `OPENAI_API_KEY`: Required for OpenAI models.
- `ANTHROPIC_API_KEY`: Required for Anthropic models.
- `API_KEY`: Generic fallback for other providers supported by the `instructor` library.

## Free Tier Setup (Recommended for Prototyping)

You can run this plugin for free by leveraging the developer API tiers of major providers. 

> **Note**: These are separate from the free web-based "bots" (like the ChatGPT or Claude.ai chat interfaces), which are not designed for automated API access.

### Google Gemini (Easiest Free Option)
Google offers a generous free tier via **Google AI Studio**.
1.  Go to [Google AI Studio](https://aistudio.google.com/).
2.  Generate a free **API Key**.
3.  Add the key to your `ModelsBackend/.env` as `GEMINI_API_KEY`.
4.  In `config.json`, ensure your model is set to a supported model (e.g., `google/gemini-2.5-flash`).

### OpenAI & Anthropic
- Sometimes **OpenAI** and **Anthropic** offer a small amount of starting credits for new accounts, which would be plenty to test out the bot.
