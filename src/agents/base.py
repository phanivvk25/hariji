"""Base Agent interface for reasoning, planning, and tool execution."""

from abc import ABC, abstractmethod
from typing import AsyncIterator, Optional, List, Dict, Any
from src.core.models import AgentStep, ChatMessage
from src.core.providers.base import BaseLLMProvider


class BaseAgent(ABC):
    """Abstract base class for all conversational and task-oriented agents."""

    def __init__(
        self,
        name: str,
        description: str,
        llm_provider: Optional[BaseLLMProvider] = None
    ):
        self.name = name
        self.description = description
        self.llm_provider = llm_provider

    @abstractmethod
    async def run(
        self,
        query: str,
        history: Optional[List[ChatMessage]] = None,
        **kwargs
    ) -> AsyncIterator[AgentStep]:
        """Execute agent workflow yielding reasoning steps and final output."""
        pass
