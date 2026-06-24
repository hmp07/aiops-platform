from abc import ABC, abstractmethod
from uuid import UUID


class IAuthService(ABC):
    @abstractmethod
    async def login(self, username: str, password: str) -> dict: ...

    @abstractmethod
    async def validate_token(self, token: str) -> dict: ...

    @abstractmethod
    async def change_password(self, user_id: UUID, old_password: str, new_password: str): ...


class IUserService(ABC):
    @abstractmethod
    async def create_user(self, data: dict) -> dict: ...

    @abstractmethod
    async def get_user(self, user_id: UUID) -> dict | None: ...

    @abstractmethod
    async def list_users(self, page: int, page_size: int, role: str | None) -> tuple[int, list[dict]]: ...

    @abstractmethod
    async def update_user(self, user_id: UUID, data: dict) -> dict: ...

    @abstractmethod
    async def delete_user(self, user_id: UUID): ...


class IAuditService(ABC):
    @abstractmethod
    async def log(self, action: str, user_id: str | None = None, username: str | None = None,
                  resource_type: str | None = None, resource_id: str | None = None,
                  detail: str | None = None, ip_address: str | None = None): ...

    @abstractmethod
    async def query(self, page: int, page_size: int, user_id: str | None = None,
                    action: str | None = None, resource_type: str | None = None) -> tuple[int, list[dict]]: ...
