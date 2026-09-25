"""Text chunking and segmentation for RAG embedding."""

import uuid
from typing import List, Dict, Any
from src.core.models import DocumentChunk


class RecursiveCharacterChunker:
    """Splits documents into overlapping chunks based on logical boundaries (paragraphs, sentences)."""

    def __init__(self, chunk_size: int = 500, chunk_overlap: int = 50):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.separators = ["\n\n", "\n", ". ", "? ", "! ", " ", ""]

    def split_text(self, text: str) -> List[str]:
        if not text:
            return []
        
        chunks = []
        start = 0
        text_len = len(text)

        while start < text_len:
            end = start + self.chunk_size
            if end >= text_len:
                chunk = text[start:].strip()
                if chunk:
                    chunks.append(chunk)
                break

            # Find best separator before end
            best_cut = end
            for sep in self.separators:
                cut = text.rfind(sep, start, end)
                if cut != -1 and cut > start + (self.chunk_size // 2):
                    best_cut = cut + len(sep)
                    break

            chunk = text[start:best_cut].strip()
            if chunk:
                chunks.append(chunk)
            
            start = max(start + 1, best_cut - self.chunk_overlap)

        return chunks

    def chunk_documents(self, documents: List[Dict[str, Any]]) -> List[DocumentChunk]:
        all_chunks: List[DocumentChunk] = []

        for doc in documents:
            content = doc.get("content", "")
            base_meta = doc.get("metadata", {})
            raw_chunks = self.split_text(content)

            for idx, chunk_text in enumerate(raw_chunks):
                chunk_id = f"{base_meta.get('source', 'doc')}_{idx}_{uuid.uuid4().hex[:6]}"
                chunk_meta = dict(base_meta)
                chunk_meta["chunk_index"] = idx
                chunk_meta["total_chunks"] = len(raw_chunks)

                all_chunks.append(
                    DocumentChunk(
                        id=chunk_id,
                        content=chunk_text,
                        metadata=chunk_meta,
                        source=base_meta.get("source"),
                        page=base_meta.get("page")
                    )
                )

        return all_chunks
