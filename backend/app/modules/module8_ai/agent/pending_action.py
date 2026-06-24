"""PendingActionManager — two-phase safety for write operations.

When the agent needs to execute a write operation:
1. Create a pending action → agent pauses
2. SSE sends pending_action event to frontend
3. User confirms/rejects → agent resumes or aborts
"""
import asyncio
import json
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from app.config.settings import get_settings

settings = get_settings()


class PendingActionManager:
    """Manages pending action lifecycle with Redis TTL."""

    def __init__(self, redis_client=None):
        self._redis = redis_client
        self._pending: dict[str, dict[str, Any]] = {}  # fallback if no Redis

    async def create(
        self,
        session_id: str,
        tool_name: str,
        input_params: dict[str, Any],
        risk_level: str,
        risk_description: str = "",
        rollback_plan: str = "",
        user_id: str = "",
    ) -> dict[str, Any]:
        """Create a pending action. Agent pauses after this call.

        Returns the action dict that will be sent via SSE.
        """
        action_id = str(uuid.uuid4())
        timeout = settings.AGENT_APPROVAL_TIMEOUT_SECONDS
        expires_at = datetime.now(timezone.utc) + timedelta(seconds=timeout)

        action = {
            "action_id": action_id,
            "session_id": session_id,
            "tool_name": tool_name,
            "input_params": input_params,
            "risk_level": risk_level,
            "risk_description": risk_description,
            "rollback_plan": rollback_plan,
            "status": "pending",
            "expires_at": expires_at.isoformat(),
            "user_id": user_id,
        }

        # Store in Redis with TTL
        if self._redis:
            key = f"pending_action:{action_id}"
            await self._redis.set(key, json.dumps(action), ex=timeout)
        else:
            self._pending[action_id] = action

        return action

    async def wait_for_decision(self, action_id: str, timeout: int | None = None) -> str:
        """Block until user decides or timeout.

        Returns: 'approved' | 'rejected' | 'timeout'
        """
        timeout = timeout or settings.AGENT_APPROVAL_TIMEOUT_SECONDS
        deadline = asyncio.get_event_loop().time() + timeout

        while asyncio.get_event_loop().time() < deadline:
            action = await self._get_action(action_id)
            if action is None:
                return "expired"
            if action.get("status") == "approved":
                return "approved"
            if action.get("status") == "rejected":
                return "rejected"
            await asyncio.sleep(1)

        return "timeout"

    async def approve(self, action_id: str, user_id: str) -> bool:
        """Approve a pending action."""
        action = await self._get_action(action_id)
        if not action or action.get("status") != "pending":
            return False
        action["status"] = "approved"
        action["decided_at"] = datetime.now(timezone.utc).isoformat()
        action["decided_by"] = user_id
        await self._save_action(action_id, action)
        return True

    async def reject(self, action_id: str, user_id: str, reason: str = "") -> bool:
        """Reject a pending action."""
        action = await self._get_action(action_id)
        if not action or action.get("status") != "pending":
            return False
        action["status"] = "rejected"
        action["decided_at"] = datetime.now(timezone.utc).isoformat()
        action["decided_by"] = user_id
        action["rejection_reason"] = reason
        await self._save_action(action_id, action)
        return True

    async def _get_action(self, action_id: str) -> dict | None:
        if self._redis:
            key = f"pending_action:{action_id}"
            data = await self._redis.get(key)
            return json.loads(data) if data else None
        return self._pending.get(action_id)

    async def _save_action(self, action_id: str, action: dict):
        if self._redis:
            key = f"pending_action:{action_id}"
            ttl = settings.AGENT_APPROVAL_TIMEOUT_SECONDS
            await self._redis.set(key, json.dumps(action), ex=ttl)
        else:
            self._pending[action_id] = action
