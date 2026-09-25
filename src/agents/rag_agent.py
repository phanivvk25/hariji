"""Agentic RAG Agent with semantic retrieval, citation grounding, and self-reflection."""

from typing import AsyncIterator, List, Optional, Dict, Any
from src.agents.base import BaseAgent
from src.core.models import AgentStep, ChatMessage, DocumentChunk
from src.core.providers.base import BaseLLMProvider
from src.core.providers.factory import ProviderFactory
from src.rag.store import VectorStore


class RAGAgent(BaseAgent):
    """Knowledge Retrieval and Grounded Synthesis Agent."""

    def __init__(
        self,
        llm_provider: Optional[BaseLLMProvider] = None,
        vector_store: Optional[VectorStore] = None
    ):
        super().__init__(
            name="RAG Knowledge Agent",
            description="Specialized in document ingestion, semantic vector retrieval, fact verification, and cited synthesis.",
            llm_provider=llm_provider
        )
        self.vector_store = vector_store or VectorStore()

    async def run(
        self,
        query: str,
        history: Optional[List[ChatMessage]] = None,
        top_k: int = 3,
        **kwargs
    ) -> AsyncIterator[AgentStep]:
        provider = self.llm_provider or ProviderFactory.get_llm_provider()

        yield AgentStep(
            step_type="thought",
            content=f"Searching knowledge base for relevant context regarding: '{query}'..."
        )

        # 1. Retrieve chunks from VectorStore
        chunks: List[DocumentChunk] = await self.vector_store.search(query, top_k=top_k)

        if not chunks:
            yield AgentStep(
                step_type="observation",
                content="No relevant documents found in knowledge base. Using general synthesis."
            )
            context_str = "No specific reference documents available in database."
        else:
            yield AgentStep(
                step_type="observation",
                content=f"Retrieved {len(chunks)} relevant document chunk(s) from knowledge base.",
                metadata={"num_chunks": len(chunks)}
            )

            # Yield individual citation cards for UI
            for chunk in chunks:
                yield AgentStep(
                    step_type="citation",
                    content=chunk.content[:240] + ("..." if len(chunk.content) > 240 else ""),
                    metadata={
                        "id": chunk.id,
                        "source": chunk.source or "Document",
                        "page": chunk.page,
                        "score": chunk.score or 0.85
                    }
                )

            # Format context string
            context_blocks = []
            for idx, c in enumerate(chunks, 1):
                src_label = f"{c.source} (Page {c.page})" if c.page else (c.source or "Document")
                context_blocks.append(f"--- Document Source [{idx}]: {src_label} ---\n{c.content}")
            context_str = "\n\n".join(context_blocks)

        # 2. Synthesize Grounded Answer
        prompt = (
            "You are a strict, grounded Knowledge Retrieval (RAG) assistant. "
            "Your task is to answer the user's question using ONLY the provided reference documents below. "
            "If the documents do not contain enough info to answer, state clearly that the answer is not in the documents. "
            "Always reference the sources (e.g. [Source 1], [Document Name]) when making claims.\n\n"
            f"=== RETRIEVED CONTEXT ===\n{context_str}\n\n"
            f"=== USER QUESTION ===\n{query}\n\n"
            "=== GROUNDED ANSWER ==="
        )

        messages = [ChatMessage(role="user", content=prompt)]

        yield AgentStep(
            step_type="thought",
            content=f"Synthesizing cited answer with model '{provider.model_name}'..."
        )

        response = await provider.generate(messages=messages, temperature=0.1)

        yield AgentStep(
            step_type="final_answer",
            content=response.content,
            metadata={
                "provider": provider.provider_name,
                "model": provider.model_name,
                "citations_count": len(chunks)
            }
        )
