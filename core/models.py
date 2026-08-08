"""LLM and embedding model factory.

Use ``get_llm()`` and ``get_embeddings()`` everywhere in the project.
Swap providers by changing LLM_PROVIDER in your .env file.
"""
from __future__ import annotations

from functools import lru_cache
from typing import Any

from core.config import settings


@lru_cache(maxsize=1)
def get_llm(temperature: float = 0.3) -> Any:
    """Return a configured chat model based on the LLM_PROVIDER setting.

    Supported providers: ``groq``, ``openai``, ``google``.
    Falls back to Groq if provider is unknown.
    """
    provider = settings.LLM_PROVIDER.lower()

    if provider == "openai":
        from langchain_openai import ChatOpenAI

        return ChatOpenAI(
            model=settings.OPENAI_MODEL,
            api_key=settings.OPENAI_API_KEY,
            temperature=temperature,
        )

    if provider == "google":
        from langchain_google_genai import ChatGoogleGenerativeAI

        return ChatGoogleGenerativeAI(
            model=settings.GOOGLE_MODEL,
            google_api_key=settings.GOOGLE_API_KEY,
            temperature=temperature,
        )

    # Default: Groq
    from langchain_groq import ChatGroq

    return ChatGroq(
        model=settings.GROQ_MODEL,
        api_key=settings.GROQ_API_KEY,
        temperature=temperature,
    )


@lru_cache(maxsize=1)
def get_embeddings() -> Any:
    """Return a local HuggingFace sentence-transformer embedding model.

    No API key required — runs fully offline after the first download.
    """
    from langchain_huggingface import HuggingFaceEmbeddings

    return HuggingFaceEmbeddings(
        model_name=settings.EMBEDDING_MODEL,
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True},
    )
