from abc import ABC, abstractmethod
from typing import Any


class BaseAdapter(ABC):
    """Abstract base for all external system adapters."""

    @abstractmethod
    async def health_check(self) -> bool:
        """Return True if the external system is reachable."""

    @abstractmethod
    async def close(self):
        """Release any connections or resources."""
