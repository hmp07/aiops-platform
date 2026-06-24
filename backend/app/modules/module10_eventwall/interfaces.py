from abc import ABC, abstractmethod
from typing import Any


class IEventService(ABC):
    """Public interface for publishing and querying EventWall events."""

    @abstractmethod
    async def publish(
        self,
        event_type: str,
        source_module: str,
        resource_type: str | None = None,
        resource_id: str | None = None,
        resource_name: str | None = None,
        payload: dict[str, Any] | None = None,
        severity: str = "info",
        correlation_id: str | None = None,
        parent_event_id: str | None = None,
        fault_id: str | None = None,
        producer_type: str = "system",
        producer_user_id: str | None = None,
        tags: dict[str, str] | None = None,
    ) -> str: ...

    @abstractmethod
    async def query_events(
        self,
        page: int = 1,
        page_size: int = 50,
        event_type: str | None = None,
        source_module: str | None = None,
        resource_type: str | None = None,
        resource_id: str | None = None,
        correlation_id: str | None = None,
        fault_id: str | None = None,
        severity: str | None = None,
        start_time: str | None = None,
        end_time: str | None = None,
    ) -> tuple[int, list[dict[str, Any]]]: ...

    @abstractmethod
    async def get_event(self, event_id: str) -> dict[str, Any] | None: ...

    @abstractmethod
    async def get_event_chain(self, correlation_id: str) -> list[dict[str, Any]]: ...


class IFaultAnalysisService(ABC):
    """Fault analysis — correlation-based clustering and scoring."""

    @abstractmethod
    async def analyze_window(
        self, window_seconds: int = 300
    ) -> list[dict[str, Any]]: ...

    @abstractmethod
    async def get_fault(self, fault_id: str) -> dict[str, Any] | None: ...

    @abstractmethod
    async def list_faults(
        self, page: int = 1, page_size: int = 20, resolved: bool = False
    ) -> tuple[int, list[dict[str, Any]]]: ...

    @abstractmethod
    async def resolve_fault(self, fault_id: str): ...
