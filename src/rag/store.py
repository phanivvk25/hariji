"""Vector Store abstraction supporting ChromaDB and resilient Cosine fallback."""

import json
import math
from pathlib import Path
from typing import List, Dict, Any, Optional
from src.config import settings
from src.core.models import DocumentChunk
from src.core.providers.base import BaseEmbeddingProvider
from src.core.providers.factory import ProviderFactory

try:
    import chromadb
    CHROMADB_AVAILABLE = True
except ImportError:
    CHROMADB_AVAILABLE = False


def cosine_similarity(vec_a: List[float], vec_b: List[float]) -> float:
    dot_product = sum(a * b for a, b in zip(vec_a, vec_b))
    norm_a = math.sqrt(sum(a * a for a in vec_a))
    norm_b = math.sqrt(sum(b * b for b in vec_b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot_product / (norm_a * norm_b)


class VectorStore:
    """Hybrid Vector Store capable of running ChromaDB or zero-dependency Cosine persistence."""

    def __init__(
        self,
        persist_dir: Optional[Path] = None,
        embedding_provider: Optional[BaseEmbeddingProvider] = None,
        collection_name: str = "agent_knowledge"
    ):
        self.persist_dir = Path(persist_dir or settings.VECTOR_DB_DIR)
        self.persist_dir.mkdir(parents=True, exist_ok=True)
        self.collection_name = collection_name
        self.embedder = embedding_provider or ProviderFactory.get_embedding_provider()
        
        # Local fallback database index file
        self._index_file = self.persist_dir / f"{collection_name}_index.json"
        self._chunks: List[Dict[str, Any]] = []
        self._load_fallback_index()

        self._chroma_client = None
        self._chroma_collection = None
        if CHROMADB_AVAILABLE:
            try:
                self._chroma_client = chromadb.PersistentClient(path=str(self.persist_dir))
                self._chroma_collection = self._chroma_client.get_or_create_collection(
                    name=collection_name
                )
            except Exception as e:
                print(f"Notice: ChromaDB init fallback to local vector store: {e}")

    def _load_fallback_index(self):
        if self._index_file.exists():
            try:
                with open(self._index_file, "r", encoding="utf-8") as f:
                    self._chunks = json.load(f)
            except Exception:
                self._chunks = []

    def _save_fallback_index(self):
        with open(self._index_file, "w", encoding="utf-8") as f:
            json.dump(self._chunks, f, ensure_ascii=False, indent=2)

    async def add_documents(self, chunks: List[DocumentChunk]) -> int:
        if not chunks:
            return 0

        texts = [chunk.content for chunk in chunks]
        embeddings = await self.embedder.embed_documents(texts)

        # 1. Update fallback store
        for chunk, emb in zip(chunks, embeddings):
            # Check if chunk id already exists
            existing = next((i for i, c in enumerate(self._chunks) if c["id"] == chunk.id), None)
            record = {
                "id": chunk.id,
                "content": chunk.content,
                "metadata": chunk.metadata,
                "source": chunk.source,
                "page": chunk.page,
                "embedding": emb
            }
            if existing is not None:
                self._chunks[existing] = record
            else:
                self._chunks.append(record)
        self._save_fallback_index()

        # 2. Update ChromaDB if active
        if self._chroma_collection:
            try:
                ids = [c.id for c in chunks]
                metadatas = [{k: str(v) for k, v in c.metadata.items()} for c in chunks]
                self._chroma_collection.upsert(
                    ids=ids,
                    documents=texts,
                    embeddings=embeddings,
                    metadatas=metadatas
                )
            except Exception as e:
                print(f"ChromaDB upsert notice: {e}")

        return len(chunks)

    async def search(self, query: str, top_k: int = 4) -> List[DocumentChunk]:
        if not self._chunks:
            return []

        query_emb = await self.embedder.embed_query(query)
        scored_chunks = []

        for record in self._chunks:
            emb = record.get("embedding", [])
            score = cosine_similarity(query_emb, emb) if emb else 0.0
            
            # Simple keyword boost if query words exist in chunk
            q_terms = [w.lower() for w in query.split() if len(w) > 3]
            content_lower = record["content"].lower()
            keyword_matches = sum(1 for term in q_terms if term in content_lower)
            if keyword_matches > 0:
                score += min(0.15, keyword_matches * 0.05)

            scored_chunks.append((score, record))

        # Sort descending by score
        scored_chunks.sort(key=lambda x: x[0], reverse=True)
        top_matches = scored_chunks[:top_k]

        results = []
        for score, record in top_matches:
            results.append(
                DocumentChunk(
                    id=record["id"],
                    content=record["content"],
                    metadata=record.get("metadata", {}),
                    score=round(score, 4),
                    source=record.get("source"),
                    page=record.get("page")
                )
            )

        return results

    def get_stats(self) -> Dict[str, Any]:
        sources = set(c.get("source") for c in self._chunks if c.get("source"))
        return {
            "total_chunks": len(self._chunks),
            "sources_count": len(sources),
            "sources": list(sources),
            "active_embedder": self.embedder.provider_name,
            "vector_backend": "ChromaDB + CosineStore" if self._chroma_collection else "CosineStore"
        }
