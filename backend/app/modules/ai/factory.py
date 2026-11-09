"""
LLM Model Factory & Provider Adapter.

Instantiates standard LangChain BaseChatModel instances configured for any provider:
- Groq (Cloud, high-speed Llama 3.3, free tier)
- xAI Grok (grok-beta / grok-2)
- Google Gemini (gemini-1.5-flash / gemini-2.0 via OpenAI-compatible endpoint)
- OpenAI (gpt-4o / gpt-4o-mini)
- Ollama (Local offline models)
- Custom OpenAI-compatible gateways
"""

from typing import Any

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_openai import ChatOpenAI

from app.core.config import Settings, get_settings

PROVIDER_DEFAULT_URLS: dict[str, str | None] = {
    "groq": "https://api.groq.com/openai/v1",
    "grok": "https://api.x.ai/v1",
    "gemini": "https://generativelanguage.googleapis.com/v1beta/openai/",
    "ollama": "http://localhost:11434/v1",
    "openai": None,  # Uses official OpenAI base URL
    "custom": None,
}


def get_chat_model(
    settings: Settings | None = None,
    **kwargs: Any,
) -> BaseChatModel:
    """
    Constructs and returns an initialized Chat model adhering to LangChain's
    BaseChatModel interface.

    Args:
        settings: Application Settings instance (defaults to cached settings).
        **kwargs: Optional runtime overrides (e.g. temperature, model, api_key).

    Returns:
        BaseChatModel instance ready for LangGraph tool-binding and invocation.
    """
    cfg = settings or get_settings()
    provider = kwargs.get("provider", cfg.AI_PROVIDER).lower().strip()

    # Determine base URL
    if "base_url" in kwargs:
        base_url = kwargs["base_url"]
    elif cfg.AI_API_BASE:
        base_url = cfg.AI_API_BASE
    else:
        base_url = PROVIDER_DEFAULT_URLS.get(provider)

    # Determine API key (fallback order: kwargs -> AI_API_KEY -> OPENAI_API_KEY -> placeholder)
    api_key = (
        kwargs.get("api_key")
        or cfg.AI_API_KEY
        or cfg.OPENAI_API_KEY
        or ("ollama" if provider == "ollama" else "dummy-api-key")
    )

    # Model name
    model_name = kwargs.get("model", cfg.AI_MODEL_NAME)
    temperature = kwargs.get("temperature", cfg.AI_TEMPERATURE)
    max_tokens = kwargs.get("max_tokens", cfg.AI_MAX_TOKENS)

    init_args: dict[str, Any] = {
        "model": model_name,
        "api_key": api_key,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    if base_url:
        init_args["base_url"] = base_url

    return ChatOpenAI(**init_args)
