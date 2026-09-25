"""FastAPI routes for Multi-Provider AI Agent platform."""

import json
from typing import List, Optional, Dict, Any, Literal
from fastapi import APIRouter, HTTPException, UploadFile, File
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from src.core.models_catalog import model_catalog, ModelInfo
from src.core.providers.factory import ProviderFactory
from src.core.models import ChatMessage, AgentStep
from src.agents.supervisor import SupervisorAgent
from src.agents.general_agent import GeneralAgent
from src.agents.rag_agent import RAGAgent
from src.rag.loader import DocumentLoader
from src.rag.chunker import RecursiveCharacterChunker
from src.rag.store import VectorStore
from src.tools.registry import tool_registry
from src.config import settings

router = APIRouter()

# Global instances
vector_store = VectorStore()
supervisor_agent = SupervisorAgent()


class ChatRequest(BaseModel):
    query: str
    mode: Literal["auto", "general", "rag"] = "auto"
    provider: Optional[str] = None
    model: Optional[str] = None
    history: Optional[List[ChatMessage]] = None


class ModelSelectRequest(BaseModel):
    provider: str
    model: str


class SearchQueryRequest(BaseModel):
    query: str
    top_k: int = 4


@router.get("/models")
async def get_models():
    """Retrieve all configurable AI providers and available models."""
    providers = model_catalog.get_available_providers()
    active = model_catalog.get_active_selection()
    
    details = {}
    for p in providers:
        details[p["id"]] = [m.model_dump() for m in model_catalog.get_models_for_provider(p["id"])]
        
    return {
        "providers": providers,
        "models": details,
        "active": active
    }


@router.post("/models/select")
async def select_model(req: ModelSelectRequest):
    """Change the active AI provider and model at runtime."""
    res = model_catalog.set_active_selection(req.provider, req.model)
    return {"status": "success", "active": res}


@router.post("/chat")
async def chat_endpoint(req: ChatRequest):
    """Execute agent workflow with event streaming response."""
    # Resolve provider and model
    active_selection = model_catalog.get_active_selection()
    target_provider = req.provider or active_selection["provider"]
    target_model = req.model or active_selection["model"]

    # Instantiate provider
    llm = ProviderFactory.get_llm_provider(
        provider_type=target_provider,
        model_name=target_model
    )

    async def event_generator():
        # Instantiate agent with requested provider
        if req.mode == "rag":
            agent = RAGAgent(llm_provider=llm, vector_store=vector_store)
            async for step in agent.run(req.query, history=req.history):
                yield f"data: {json.dumps(step.model_dump())}\n\n"
        elif req.mode == "general":
            agent = GeneralAgent(llm_provider=llm, tools=tool_registry)
            async for step in agent.run(req.query, history=req.history):
                yield f"data: {json.dumps(step.model_dump())}\n\n"
        else:
            agent = SupervisorAgent(
                llm_provider=llm,
                general_agent=GeneralAgent(llm_provider=llm, tools=tool_registry),
                rag_agent=RAGAgent(llm_provider=llm, vector_store=vector_store)
            )
            async for step in agent.run(req.query, history=req.history, mode="auto"):
                yield f"data: {json.dumps(step.model_dump())}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router.get("/knowledge/stats")
async def get_knowledge_stats():
    """Get vector store index statistics and sources."""
    return vector_store.get_stats()


@router.post("/knowledge/ingest/directory")
async def ingest_raw_directory():
    """Scan and index all files in data/raw."""
    loader = DocumentLoader()
    raw_docs = loader.load_directory(settings.DOCS_RAW_DIR)
    
    if not raw_docs:
        return {"status": "no_documents_found", "chunks_added": 0}

    chunker = RecursiveCharacterChunker(chunk_size=400, chunk_overlap=40)
    chunks = chunker.chunk_documents(raw_docs)
    added = await vector_store.add_documents(chunks)
    
    return {
        "status": "success",
        "raw_docs_processed": len(raw_docs),
        "chunks_indexed": added,
        "stats": vector_store.get_stats()
    }


@router.post("/knowledge/upload")
async def upload_document(file: UploadFile = File(...)):
    """Upload and immediately chunk & index a document."""
    target_path = settings.DOCS_RAW_DIR / file.filename
    content = await file.read()
    with open(target_path, "wb") as f:
        f.write(content)

    docs = DocumentLoader.load_file(target_path)
    chunker = RecursiveCharacterChunker()
    chunks = chunker.chunk_documents(docs)
    added = await vector_store.add_documents(chunks)

    return {
        "filename": file.filename,
        "chunks_added": added,
        "total_stats": vector_store.get_stats()
    }


@router.post("/knowledge/query")
async def query_knowledge(req: SearchQueryRequest):
    """Direct vector search query to inspect retrieval performance and scores."""
    chunks = await vector_store.search(req.query, top_k=req.top_k)
    return {"results": [c.model_dump() for c in chunks]}


@router.get("/tools")
async def list_tools():
    """List registered tools."""
    return {
        "tools": [t.model_dump() for t in tool_registry.list_definitions()]
    }
