"""Abstract base class for all agents."""
from __future__ import annotations

from abc import ABC
from typing import Any


class BaseAgent(ABC):
    """Provides a lazily-initialised LLM instance for all concrete agents.

    The LLM is only created the first time ``.llm`` is accessed, so agents
    whose CRUD operations don't need the model (e.g. notes, tasks) work fine
    even when no API key is set.
    """

    def __init__(self) -> None:
        self._llm: Any | None = None

    @property
    def llm(self) -> Any:
        """Return the shared LLM, initialising it on first access."""
        if self._llm is None:
            from core.models import get_llm

            self._llm = get_llm()
        return self._llm

    @llm.setter
    def llm(self, value: Any) -> None:
        self._llm = value

    @property
    def name(self) -> str:
        """Human-readable agent name (class name by default)."""
        return self.__class__.__name__
