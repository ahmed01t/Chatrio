"""
Sliding Window Debounce Buffer for WhatsApp Messaging.

Coalesces rapid multi-message bursts from a customer into a single conversational turn:
1. Sliding Inactivity Timer (default 2.5s): Resets every time a customer sends another message.
2. Hard Maximum Wait Ceiling (default 8.0s): Flushes automatically if continuous typing
   reaches the cap.
3. Dual-mode support: Uses Redis for production clustering, with an in-memory fallback
   for local testing.
"""

import json
import time
from typing import Any

from redis.asyncio import Redis

from app.core.config import get_settings


class SlidingDebounceBuffer:
    """
    Manages sliding-window message aggregation per customer phone number.
    """

    def __init__(
        self,
        redis_client: Redis | None = None,
        inactivity_seconds: float | None = None,
        max_wait_seconds: float | None = None,
    ) -> None:
        settings = get_settings()
        self.redis = redis_client
        self.inactivity_seconds = (
            inactivity_seconds
            if inactivity_seconds is not None
            else settings.WHATSAPP_DEBOUNCE_SECONDS
        )
        self.max_wait_seconds = (
            max_wait_seconds
            if max_wait_seconds is not None
            else settings.WHATSAPP_DEBOUNCE_MAX_WAIT_SECONDS
        )

        # In-memory store fallback when Redis is not provided (used in unit tests / local dev)
        # Format: {phone_number: {"first_at": float, "last_at": float, "messages": list[dict]}}
        self._memory_store: dict[str, dict[str, Any]] = {}

    def _redis_keys(self, phone_number: str) -> tuple[str, str]:
        """Returns Redis keys for messages list and burst metadata."""
        clean_phone = phone_number.replace("+", "").strip()
        msg_key = f"whatsapp:debounce:{clean_phone}:messages"
        meta_key = f"whatsapp:debounce:{clean_phone}:meta"
        return msg_key, meta_key

    async def add_message(
        self,
        phone_number: str,
        message: dict[str, Any],
        current_time: float | None = None,
    ) -> tuple[bool, list[dict[str, Any]] | None]:
        """
        Adds a message to the debounce buffer for the given customer.

        Returns:
            (should_flush_now, coalesced_messages):
            - If the hard max wait ceiling is exceeded: (True, [all_messages])
            - If still buffering and timer was reset: (False, None)
        """
        now = current_time if current_time is not None else time.time()

        if self.redis is not None:
            return await self._add_redis(phone_number, message, now)
        return self._add_memory(phone_number, message, now)

    async def _add_redis(
        self,
        phone_number: str,
        message: dict[str, Any],
        now: float,
    ) -> tuple[bool, list[dict[str, Any]] | None]:
        assert self.redis is not None
        msg_key, meta_key = self._redis_keys(phone_number)

        # Read or initialize first_at timestamp
        meta = await self.redis.hgetall(meta_key)
        first_at_raw = meta.get(b"first_at") or meta.get("first_at")

        if first_at_raw is None:
            first_at = now
            await self.redis.hset(meta_key, "first_at", str(first_at))
        else:
            first_at = float(first_at_raw)

        # Push message JSON to list
        serialized = json.dumps(message)
        await self.redis.rpush(msg_key, serialized)

        # Check if hard maximum wait ceiling is reached
        elapsed = now - first_at
        if elapsed >= self.max_wait_seconds:
            # Flush immediately: hard cap reached
            messages = await self.flush(phone_number)
            return True, messages

        # Otherwise, refresh sliding expiration window on both keys
        ttl = int(self.inactivity_seconds) + 1
        await self.redis.expire(msg_key, ttl)
        await self.redis.expire(meta_key, int(self.max_wait_seconds) + 1)
        return False, None

    def _add_memory(
        self,
        phone_number: str,
        message: dict[str, Any],
        now: float,
    ) -> tuple[bool, list[dict[str, Any]] | None]:
        clean_phone = phone_number.replace("+", "").strip()

        if clean_phone not in self._memory_store:
            self._memory_store[clean_phone] = {
                "first_at": now,
                "last_at": now,
                "messages": [message],
            }
            return False, None

        state = self._memory_store[clean_phone]
        first_at = state["first_at"]
        state["last_at"] = now
        state["messages"].append(message)

        elapsed = now - first_at
        if elapsed >= self.max_wait_seconds:
            # Hard max ceiling reached
            flushed = state["messages"]
            del self._memory_store[clean_phone]
            return True, flushed

        return False, None

    async def flush(self, phone_number: str) -> list[dict[str, Any]]:
        """
        Atomically extracts and clears all buffered messages for the customer.
        """
        if self.redis is not None:
            return await self._flush_redis(phone_number)
        return self._flush_memory(phone_number)

    async def _flush_redis(self, phone_number: str) -> list[dict[str, Any]]:
        assert self.redis is not None
        msg_key, meta_key = self._redis_keys(phone_number)

        # Atomically fetch and delete via pipeline
        pipe = self.redis.pipeline()
        pipe.lrange(msg_key, 0, -1)
        pipe.delete(msg_key)
        pipe.delete(meta_key)
        results = await pipe.execute()

        raw_messages = results[0]
        messages: list[dict[str, Any]] = []
        for item in raw_messages:
            val = item.decode("utf-8") if isinstance(item, bytes) else str(item)
            messages.append(json.loads(val))

        return messages

    def _flush_memory(self, phone_number: str) -> list[dict[str, Any]]:
        clean_phone = phone_number.replace("+", "").strip()
        state = self._memory_store.pop(clean_phone, None)
        if state is None:
            return []
        return state["messages"]

    def is_silence_expired(self, phone_number: str, current_time: float) -> bool:
        """
        Checks if the customer has stopped typing for longer than the inactivity window.
        (Used by background polling / worker tasks).
        """
        clean_phone = phone_number.replace("+", "").strip()
        state = self._memory_store.get(clean_phone)
        if not state:
            return False

        last_at = state["last_at"]
        return (current_time - last_at) >= self.inactivity_seconds

    @staticmethod
    def coalesce_texts(messages: list[dict[str, Any]]) -> str:
        """
        Combines multiple incoming text fragments into a single coherent turn string.
        """
        bodies = [m.get("text", "").strip() for m in messages if m.get("text", "").strip()]
        return "\n".join(bodies)
