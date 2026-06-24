from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.module9_platform.models import ApiToken, AuditLog, User


class UserRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def create(self, user_data: dict) -> User:
        user = User(**user_data)
        self._session.add(user)
        await self._session.commit()
        await self._session.refresh(user)
        return user

    async def get_by_id(self, user_id: UUID) -> User | None:
        return await self._session.get(User, user_id)

    async def get_by_username(self, username: str) -> User | None:
        result = await self._session.execute(select(User).where(User.username == username))
        return result.scalar_one_or_none()

    async def list_users(self, page: int, page_size: int, role: str | None = None) -> tuple[int, list[User]]:
        query = select(User)
        count_query = select(func.count(User.id))
        if role:
            query = query.where(User.role == role)
            count_query = count_query.where(User.role == role)
        query = query.order_by(User.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
        total = (await self._session.execute(count_query)).scalar() or 0
        result = await self._session.execute(query)
        return total, list(result.scalars().all())

    async def update(self, user: User, data: dict) -> User:
        for key, value in data.items():
            if value is not None:
                setattr(user, key, value)
        await self._session.commit()
        await self._session.refresh(user)
        return user

    async def delete(self, user: User):
        await self._session.delete(user)
        await self._session.commit()


class AuditRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def create(self, data: dict) -> AuditLog:
        entry = AuditLog(**data)
        self._session.add(entry)
        await self._session.commit()
        return entry

    async def query(
        self, page: int, page_size: int,
        user_id: str | None = None, action: str | None = None, resource_type: str | None = None,
    ) -> tuple[int, list[AuditLog]]:
        query = select(AuditLog)
        count_query = select(func.count(AuditLog.id))
        if user_id:
            query = query.where(AuditLog.user_id == user_id)
            count_query = count_query.where(AuditLog.user_id == user_id)
        if action:
            query = query.where(AuditLog.action == action)
            count_query = count_query.where(AuditLog.action == action)
        if resource_type:
            query = query.where(AuditLog.resource_type == resource_type)
            count_query = count_query.where(AuditLog.resource_type == resource_type)
        query = query.order_by(AuditLog.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
        total = (await self._session.execute(count_query)).scalar() or 0
        result = await self._session.execute(query)
        return total, list(result.scalars().all())


class ApiTokenRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def create(self, data: dict) -> ApiToken:
        token = ApiToken(**data)
        self._session.add(token)
        await self._session.commit()
        await self._session.refresh(token)
        return token

    async def list_by_user(self, user_id: UUID) -> list[ApiToken]:
        result = await self._session.execute(
            select(ApiToken).where(ApiToken.user_id == user_id).order_by(ApiToken.created_at.desc())
        )
        return list(result.scalars().all())

    async def revoke(self, token: ApiToken):
        token.is_active = False
        await self._session.commit()
