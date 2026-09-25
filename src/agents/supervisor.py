"""Supervisor / Router Agent orchestrating General LLM and RAG Agents."""

from typing import AsyncIterator, List, Optional, Literal
from src.agents.base import BaseAgent
from src.agents.general_agent import GeneralAgent
from src.agents.rag_agent import RAGAgent
from src.core.models import AgentStep, ChatMessage
from src.core.providers.base import BaseLLMProvider


class SupervisorAgent(BaseAgent):
    """Orchestrates workflows across General LLM and RAG Agents."""

    def __init__(
        self,
        llm_provider: Optional[BaseLLMProvider] = None,
        general_agent: Optional[GeneralAgent] = None,
        rag_agent: Optional[RAGAgent] = None
    ):
        super().__init__(
            name="Supervisor Orchestrator",
            description="Intelligently classifies tasks and routes them to General Reasoning or RAG Knowledge agents.",
            llm_provider=llm_provider
        )
        self.general_agent = general_agent or GeneralAgent(llm_provider=llm_provider)
        self.rag_agent = rag_agent or RAGAgent(llm_provider=llm_provider)

    def classify_intent(self, query: str) -> Literal["rag", "general", "hybrid"]:
        q = query.lower()
        
        # Knowledge / Document keywords
        rag_triggers = [
            "document", "doc", "pdf", "file", "knowledge", "policy", "handbook",
            "according to", "what does the text say", "summary of the report", "internal",
            "cite", "source"
        ]
        
        # Calculation / Tool triggers
        general_triggers = [
            "calculate", "compute", "math", "evaluate", "search web", "weather",
            "time", "clock", "+", "-", "*", "/", "sqrt", "now"
        ]

        has_rag = any(t in q for t in rag_triggers)
        has_general = any(t in q for t in general_triggers)

        if has_rag and has_general:
            return "hybrid"
        elif has_rag:
            return "rag"
        else:
            return "general"

    async def run(
        self,
        query: str,
        history: Optional[List[ChatMessage]] = None,
        mode: Literal["auto", "general", "rag"] = "auto",
        **kwargs
    ) -> AsyncIterator[AgentStep]:
        # Determine target agent
        target_mode = mode
        if target_mode == "auto":
            inferred = self.classify_intent(query)
            yield AgentStep(
                step_type="thought",
                content=f"Supervisor classification: Identified intent as `{inferred}`. Routing query accordingly."
            )
            target_mode = "rag" if inferred == "rag" else "general"

        if target_mode == "rag":
            yield AgentStep(
                step_type="thought",
                content="[Supervisor] Delegating query to RAG Knowledge Agent."
            )
            async for step in self.rag_agent.run(query, history=history, **kwargs):
                yield step

        else:
            yield AgentStep(
                step_type="thought",
                content="[Supervisor] Delegating query to General Reasoning Agent."
            )
            async for step in self.general_agent.run(query, history=history, **kwargs):
                yield step
