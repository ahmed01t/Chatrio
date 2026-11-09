"""
Unit tests for AI Model Factory & Provider Adapters.

Validates:
1. Dynamic provider resolution (Groq, Grok, Gemini, OpenAI, Ollama).
2. Proper base URL injection per provider.
3. Fallback resolution for API keys and default models.
"""

from app.core.config import Settings
from app.modules.ai.factory import get_chat_model


def test_factory_groq_provider() -> None:
    """Verify Groq provider uses the Groq Cloud endpoint."""
    settings = Settings(
        AI_PROVIDER="groq",
        AI_API_KEY="gsk_test123",
        AI_MODEL_NAME="llama-3.3-70b-versatile",
    )
    model = get_chat_model(settings)
    assert model.model_name == "llama-3.3-70b-versatile"
    assert "api.groq.com" in str(model.openai_api_base)


def test_factory_grok_provider() -> None:
    """Verify xAI Grok provider uses the xAI endpoint."""
    settings = Settings(
        AI_PROVIDER="grok",
        AI_API_KEY="xai-test456",
        AI_MODEL_NAME="grok-beta",
    )
    model = get_chat_model(settings)
    assert model.model_name == "grok-beta"
    assert "api.x.ai" in str(model.openai_api_base)


def test_factory_gemini_provider() -> None:
    """Verify Google Gemini provider uses the Google OpenAI endpoint."""
    settings = Settings(
        AI_PROVIDER="gemini",
        AI_API_KEY="AIzaSyTest",
        AI_MODEL_NAME="gemini-1.5-flash",
    )
    model = get_chat_model(settings)
    assert model.model_name == "gemini-1.5-flash"
    assert "generativelanguage.googleapis.com" in str(model.openai_api_base)


def test_factory_ollama_provider() -> None:
    """Verify local Ollama provider uses localhost:11434."""
    settings = Settings(
        AI_PROVIDER="ollama",
        AI_MODEL_NAME="llama3.1",
    )
    model = get_chat_model(settings)
    assert model.model_name == "llama3.1"
    assert "localhost:11434" in str(model.openai_api_base)


def test_factory_custom_base_url_override() -> None:
    """Verify custom base URL override takes precedence."""
    settings = Settings(
        AI_PROVIDER="custom",
        AI_API_BASE="https://my-custom-proxy.internal/v1",
        AI_MODEL_NAME="custom-model",
    )
    model = get_chat_model(settings)
    assert "my-custom-proxy.internal" in str(model.openai_api_base)
