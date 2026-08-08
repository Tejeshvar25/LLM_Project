"""Vector store management: ingest documents and query via ChromaDB.

Workflow
--------
1. Upload files → ``build_chroma_db_from_uploads()`` saves them to disk,
   splits into chunks, embeds with HuggingFace, and stores in ChromaDB.
2. At query time → ``get_retriever()`` loads the persisted collection and
   returns a LangChain retriever ready for RAG.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_community.vectorstores import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter

from core.config import settings
from core.models import get_embeddings


# ── Helpers ──────────────────────────────────────────────────────────────────


def _load_file(file_path: str) -> list:
    """Load a document using the appropriate loader for its extension."""
    ext = Path(file_path).suffix.lower()
    if ext == ".pdf":
        return PyPDFLoader(file_path).load()
    return TextLoader(file_path, encoding="utf-8").load()


# ── Public API ───────────────────────────────────────────────────────────────


def build_chroma_db_from_uploads(uploaded_files: list[dict]) -> dict:
    """Process uploaded files and (re)build the ChromaDB collection.

    Args:
        uploaded_files: List of ``{"name": str, "data": bytes}`` dicts from
            Streamlit's file uploader.

    Returns:
        ``{"success": True, "num_chunks": int}`` or
        ``{"success": False, "error": str}``.
    """
    try:
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.CHUNK_SIZE,
            chunk_overlap=settings.CHUNK_OVERLAP,
        )
        all_docs = []

        for file_info in uploaded_files:
            save_path = settings.UPLOADS_DIR / file_info["name"]
            save_path.write_bytes(file_info["data"])

            raw_docs = _load_file(str(save_path))
            chunks = splitter.split_documents(raw_docs)
            all_docs.extend(chunks)

        if not all_docs:
            return {"success": False, "error": "No text could be extracted from the uploaded files."}

        embeddings = get_embeddings()
        Chroma.from_documents(
            documents=all_docs,
            embedding=embeddings,
            persist_directory=settings.CHROMA_DIR,
            collection_name=settings.CHROMA_COLLECTION,
        )

        return {"success": True, "num_chunks": len(all_docs)}

    except Exception as exc:  # noqa: BLE001
        return {"success": False, "error": str(exc)}


def get_vectorstore() -> Chroma | None:
    """Load the persisted ChromaDB collection.

    Returns ``None`` if the collection is empty or the directory is missing.
    """
    try:
        embeddings = get_embeddings()
        vs = Chroma(
            persist_directory=settings.CHROMA_DIR,
            embedding_function=embeddings,
            collection_name=settings.CHROMA_COLLECTION,
        )
        # Verify the collection is not empty
        if vs._collection.count() == 0:
            return None
        return vs
    except Exception:
        return None


def get_retriever(search_kwargs: dict | None = None):
    """Return a LangChain retriever from the ChromaDB collection, or ``None``."""
    vs = get_vectorstore()
    if vs is None:
        return None
    sk = search_kwargs or {"k": settings.TOP_K_RESULTS}
    return vs.as_retriever(search_type="similarity", search_kwargs=sk)


def query_knowledge_base(query: str) -> dict:
    """Run a similarity search and return top-k document chunks with scores.

    Returns:
        ``{"documents": list, "sources": list}`` or ``{"error": str}``.
    """
    vs = get_vectorstore()
    if vs is None:
        return {
            "documents": [],
            "sources": [],
            "error": "Knowledge base is empty. Upload documents and click 'Build Knowledge Base'.",
        }

    try:
        results = vs.similarity_search_with_score(query, k=settings.TOP_K_RESULTS)
        documents, sources = [], []
        for doc, score in results:
            documents.append(
                {
                    "content": doc.page_content,
                    "metadata": doc.metadata,
                    "score": round(float(score), 4),
                }
            )
            src = doc.metadata.get("source", "unknown")
            if src not in sources:
                sources.append(src)
        return {"documents": documents, "sources": sources}

    except Exception as exc:  # noqa: BLE001
        return {"documents": [], "sources": [], "error": str(exc)}
