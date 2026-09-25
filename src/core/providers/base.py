"""Abstract base classes for multi-provider LLM and Embedding services."""

from abc import ABC, abstractmethod
from typing import List, Optional, AsyncIterator, Dict, Any
from src.core.models import ChatMessage, ToolDefinition, LLMResponse


class BaseLLMProvider(ABC):
    """Abstract interface for LLM text generation and tool-calling."""

    def __init__(self, model_name: str, **kwargs):
        self.model_name = model_name
        self.kwargs = kwargs

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Name of the provider: google, openai, azure, aws_bedrock, etc."""
        pass

    @abstractmethod
    async def generate(
        self,
        messages: List[ChatMessage],
        tools: Optional[List[ToolDefinition]] = None,
        temperature: float = 0.2,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> LLMResponse:
        """Generate response from the LLM model."""
        pass

    @abstractmethod
    async def stream(
        self,
        messages: List[ChatMessage],
        tools: Optional[List[ToolDefinition]] = None,
        temperature: float = 0.2,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> AsyncIterator[str]:
        """Stream token responses from the LLM model."""
        pass


class BaseEmbeddingProvider(ABC):
    """Abstract interface for text embedding models."""

    def __init__(self, model_name: str, **kwargs):
        self.model_name = model_name
        self.kwargs = kwargs

    @property
    @abstractmethod
    def provider_name(self) -> str:
        pass

    @abstractmethod
    async def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for a list of document strings."""
        pass

    @abstractmethod
    async def embed_query(self, text: str) -> List[float]:
        """Generate embedding for a single search query."""
        pass
