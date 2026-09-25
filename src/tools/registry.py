"""Tool Registry for discovering, configuring, and executing agent tools."""

from typing import Dict, List, Optional, Any
from src.tools.base import BaseTool
from src.core.models import ToolDefinition, ToolCall
from src.tools.builtins.calculator import CalculatorTool
from src.tools.builtins.web_search import WebSearchTool, DateTimeTool


class ToolRegistry:
    """Registry maintaining available tools and execution dispatch."""

    def __init__(self):
        self._tools: Dict[str, BaseTool] = {}
        # Register standard default tools
        self.register(CalculatorTool())
        self.register(WebSearchTool())
        self.register(DateTimeTool())

    def register(self, tool: BaseTool) -> None:
        self._tools[tool.name] = tool

    def get(self, name: str) -> Optional[BaseTool]:
        return self._tools.get(name)

    def list_definitions(self) -> List[ToolDefinition]:
        return [tool.to_definition() for tool in self._tools.values()]

    def list_tool_names(self) -> List[str]:
        return list(self._tools.keys())

    async def execute(self, tool_call: ToolCall) -> Any:
        tool = self._tools.get(tool_call.name)
        if not tool:
            return f"Error: Tool '{tool_call.name}' not found in registry."
        try:
            return await tool.execute(**tool_call.arguments)
        except Exception as e:
            return f"Error executing tool '{tool_call.name}': {str(e)}"


# Singleton default registry
tool_registry = ToolRegistry()
