from functools import lru_cache
from langchain_openai import ChatOpenAI

from ..config import get_settings

@lru_cache(maxsize=1)
def create_chat_model(temperature: float = 0.0) -> ChatOpenAI:
    """Create a LangChain ChatOpenAI instance.

    Args:
        temperature: Model temperature (default: 0.0 for deterministic outputs).

    Returns:
        Configured ChatOpenAI instance.
    """
    settings = get_settings()
    return ChatOpenAI(
        model=settings.openai_model_name,
        api_key=settings.openai_api_key,
        temperature=temperature,
    )