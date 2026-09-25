import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import asyncio
from src.core.models_catalog import model_catalog
from src.core.providers.factory import ProviderFactory
from src.rag.loader import DocumentLoader
from src.rag.chunker import RecursiveCharacterChunker
from src.rag.store import VectorStore
from src.agents.supervisor import SupervisorAgent
from src.agents.general_agent import GeneralAgent
from src.agents.rag_agent import RAGAgent
from src.config import settings


async def test_system():
    print("=== TEST 1: Model Catalog & Multi-Provider Config ===")
    providers = model_catalog.get_available_providers()
    print(f"Discovered {len(providers)} providers:")
    for p in providers:
        models = model_catalog.get_models_for_provider(p["id"])
        print(f" - Provider: {p['name']} ({p['id']}) -> {len(models)} models available")
    assert len(providers) >= 4, "Should support at least 4 providers"

    print("\n=== TEST 2: Knowledge Ingestion & Vector Store ===")
    raw_docs = DocumentLoader.load_directory(settings.DOCS_RAW_DIR)
    print(f"Loaded {len(raw_docs)} source documents from data/raw/")
    chunker = RecursiveCharacterChunker(chunk_size=300, chunk_overlap=30)
    chunks = chunker.chunk_documents(raw_docs)
    print(f"Created {len(chunks)} chunks.")

    vstore = VectorStore()
    added = await vstore.add_documents(chunks)
    print(f"Added {added} chunks to VectorStore.")
    
    # Test search
    search_res = await vstore.search("security and provider isolation", top_k=2)
    print(f"Search found {len(search_res)} matching chunks.")
    for r in search_res:
        print(f"  [Score: {r.score}] Source: {r.source} -> {r.content[:70]}...")
    assert len(search_res) > 0, "Vector search should return relevant chunks"

    print("\n=== TEST 3: General LLM Agent with Tool Calling ===")
    gen_agent = GeneralAgent()
    print("Running math query through General Agent...")
    async for step in gen_agent.run("Calculate 128 * 4"):
        print(f"  Step [{step.step_type}]: {step.content[:80]}")

    print("\n=== TEST 4: RAG Knowledge Agent ===")
    rag_agent = RAGAgent(vector_store=vstore)
    print("Running RAG query...")
    async for step in rag_agent.run("What are the guidelines for chunk sizes in chapter 3?"):
        print(f"  Step [{step.step_type}]: {step.content[:80]}")

    print("\n=== TEST 5: Supervisor Intelligent Routing ===")
    supervisor = SupervisorAgent(rag_agent=rag_agent)
    print("Testing auto-routing for document question...")
    async for step in supervisor.run("What does our policy handbook say about tenant isolation?"):
        print(f"  Supervisor Step [{step.step_type}]: {step.content[:80]}")

    print("\nALL BACKEND TESTS PASSED SUCCESSFULLY!")


if __name__ == "__main__":
    asyncio.run(test_system())
