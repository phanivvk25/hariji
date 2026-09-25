"""Base definitions for agent tools."""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from src.core.models import ToolDefinition


class BaseTool(ABC):
    """Abstract base class for all tools accessible by AI agents."""

    name: str
    description: str
    parameters: Dict[str, Any]

    def to_definition(self) -> ToolDefinition:
        """Convert tool to ToolDefinition model for LLMs."""
        return ToolDefinition(
            name=self.name,
            description=self.description,
            parameters=self.parameters
        )

    @abstractmethod
    async def execute(self, **kwargs) -> Any:
        """Execute the tool function asynchronously."""
        pass
