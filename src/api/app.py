"""Main FastAPI application entry point with CORS and lifespan indexing."""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.api.routes import router, ingest_raw_directory
from src.api.portal_routes import router as portal_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: auto-index any seed documents in data/raw
    print("AI Agent Platform starting up...")
    try:
        res = await ingest_raw_directory()
        print(f"Initial knowledge base indexing complete: {res.get('chunks_indexed', 0)} chunks indexed.")
    except Exception as e:
        print(f"Notice during initial indexing: {e}")
    yield
    print("AI Agent Platform shutting down.")


app = FastAPI(
    title="Multi-Provider AI Agent Platform",
    description="Enterprise AI platform accommodating General LLM Agents, RAG Agents, and Microsoft Fluent UI v2",
    version="1.0.0",
    lifespan=lifespan
)

# Enable CORS for frontend development and production
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routes
app.include_router(router, prefix="/api")
app.include_router(portal_router, prefix="/api/portal")


@app.get("/")
async def root():
    return {
        "status": "online",
        "service": "Multi-Provider AI Agent Platform",
        "docs_url": "/docs",
        "api_prefix": "/api"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.api.app:app", host="0.0.0.0", port=8000, reload=True)
