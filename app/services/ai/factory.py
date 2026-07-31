from app.core.config import get_settings
from app.services.ai.claude import MockClaudeClient
from app.services.ai.claude_api import ClaudeAPIClient


def get_ai_client():
    settings = get_settings()

    if settings.ai_mode == "mock":
        return MockClaudeClient()

    return ClaudeAPIClient(
        api_key=settings.anthropic_api_key,
        model=settings.claude_model,
    )
