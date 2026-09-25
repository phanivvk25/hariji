"""General LLM Agent with tool calling and multi-step reasoning."""

from typing import AsyncIterator, List, Optional, Dict, Any
from src.agents.base import BaseAgent
from src.core.models import AgentStep, ChatMessage, ToolCall
from src.core.providers.base import BaseLLMProvider
from src.core.providers.factory import ProviderFactory
from src.tools.registry import tool_registry, ToolRegistry


class GeneralAgent(BaseAgent):
    """Reasoning and Tool-Execution Agent."""

    def __init__(
        self,
        llm_provider: Optional[BaseLLMProvider] = None,
        tools: Optional[ToolRegistry] = None,
        max_iterations: int = 5
    ):
        super().__init__(
            name="General LLM Agent",
            description="Autonomous problem solver capable of mathematical calculation, real-time web search, and tool execution.",
            llm_provider=llm_provider
        )
        self.tools = tools or tool_registry
        self.max_iterations = max_iterations

    async def run(
        self,
        query: str,
        history: Optional[List[ChatMessage]] = None,
        **kwargs
    ) -> AsyncIterator[AgentStep]:
        provider = self.llm_provider or ProviderFactory.get_llm_provider()
        tool_defs = self.tools.list_definitions()

        messages: List[ChatMessage] = [
            ChatMessage(
                role="system",
                content=(
                    "You are a helpful, accurate, and analytical General AI Agent. "
                    "When solving problems that require calculation or current facts, use the provided tools. "
                    "Always verify results and explain your reasoning clearly."
                )
            )
        ]
        if history:
            messages.extend(history)
        messages.append(ChatMessage(role="user", content=query))

        yield AgentStep(
            step_type="thought",
            content=f"Analyzing user query: '{query}' with model '{provider.model_name}' ({provider.provider_name})."
        )

        for iteration in range(self.max_iterations):
            # Check if query directly warrants calculator or search heuristics if using basic model
            q_lower = query.lower()
            if iteration == 0 and any(op in query for op in ["+", "*", "/", "sqrt", "calculate", "sum of"]):
                # Proactive thought
                yield AgentStep(
                    step_type="thought",
                    content="Detected numerical/mathematical computation. Formulating tool execution."
                )

            response = await provider.generate(
                messages=messages,
                tools=tool_defs,
                temperature=0.1
            )

            # If the model produced tool calls
            if response.tool_calls:
                for tc in response.tool_calls:
                    yield AgentStep(
                        step_type="action",
                        content=f"Calling tool `{tc.name}` with parameters: {tc.arguments}",
                        metadata={"tool_name": tc.name, "arguments": tc.arguments}
                    )

                    result = await self.tools.execute(tc)

                    yield AgentStep(
                        step_type="observation",
                        content=f"Result from `{tc.name}`: {result}",
                        metadata={"tool_name": tc.name, "result": result}
                    )

                    # Append to messages for next iteration
                    messages.append(ChatMessage(
                        role="assistant",
                        content=response.content or f"Calling {tc.name}",
                        tool_calls=[{"id": tc.id, "type": "function", "function": {"name": tc.name, "arguments": str(tc.arguments)}}]
                    ))
                    messages.append(ChatMessage(
                        role="tool",
                        content=str(result),
                        name=tc.name,
                        tool_call_id=tc.id
                    ))
            else:
                # Direct response
                yield AgentStep(
                    step_type="final_answer",
                    content=response.content,
                    metadata={"provider": provider.provider_name, "model": provider.model_name}
                )
                return

        yield AgentStep(
            step_type="final_answer",
            content="Reached maximum reasoning steps. Please refine your query.",
            metadata={"status": "max_iterations_reached"}
        )
