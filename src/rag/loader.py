"""Multi-format document loaders for ingestion into the RAG pipeline."""

import os
from pathlib import Path
from typing import List, Dict, Any
from src.core.models import DocumentChunk

try:
    from pypdf import PdfReader
    PYPDF_AVAILABLE = True
except ImportError:
    PYPDF_AVAILABLE = False


class DocumentLoader:
    """Loads and parses raw files from local directory or direct file paths."""

    @staticmethod
    def load_file(file_path: Path) -> List[Dict[str, Any]]:
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {path}")

        ext = path.suffix.lower()
        documents = []

        if ext in [".txt", ".md", ".json", ".csv"]:
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                text = f.read()
            documents.append({
                "content": text,
                "metadata": {
                    "source": path.name,
                    "file_path": str(path),
                    "file_type": ext.lstrip("."),
                    "size_bytes": path.stat().st_size
                }
            })

        elif ext == ".pdf":
            if not PYPDF_AVAILABLE:
                raise ImportError("pypdf is required to parse PDF files. Install via `pip install pypdf`.")
            reader = PdfReader(str(path))
            for page_idx, page in enumerate(reader.pages):
                text = page.extract_text() or ""
                if text.strip():
                    documents.append({
                        "content": text,
                        "metadata": {
                            "source": path.name,
                            "file_path": str(path),
                            "file_type": "pdf",
                            "page": page_idx + 1,
                            "total_pages": len(reader.pages)
                        }
                    })
        else:
            # Fallback text reading
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                text = f.read()
            documents.append({
                "content": text,
                "metadata": {
                    "source": path.name,
                    "file_path": str(path),
                    "file_type": "text"
                }
            })

        return documents

    @classmethod
    def load_directory(cls, dir_path: Path) -> List[Dict[str, Any]]:
        target_dir = Path(dir_path)
        if not target_dir.exists():
            return []
        
        all_docs = []
        for file in target_dir.glob("**/*"):
            if file.is_file() and file.suffix.lower() in [".txt", ".md", ".pdf", ".csv", ".json"]:
                try:
                    all_docs.extend(cls.load_file(file))
                except Exception as e:
                    print(f"Warning: Failed to load {file}: {e}")
        return all_docs
