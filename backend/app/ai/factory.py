from typing import Optional
from app.ai.base import BaseAIProvider
from app.ai.mock_provider import MockAIProvider
from app.ai.gemini_provider import GeminiProvider
from app.ai.openai_provider import OpenAIProvider
from app.core.config import settings


def get_ai_provider(provider_type: Optional[str] = None) -> BaseAIProvider:
    """Factory to retrieve configured AI Provider with fallback to Mock Provider."""
    chosen = (provider_type or settings.AI_PROVIDER).lower()

    if chosen == "gemini" and settings.AI_API_KEY:
        return GeminiProvider(api_key=settings.AI_API_KEY, model_name=settings.AI_MODEL)
    elif chosen in {"openai", "anthropic"} and settings.AI_API_KEY:
        return OpenAIProvider(api_key=settings.AI_API_KEY, model_name=settings.AI_MODEL)
    else:
        # Default or fallback to deterministic mock provider
        return MockAIProvider(model_name="patchpilot-mock-v1")

