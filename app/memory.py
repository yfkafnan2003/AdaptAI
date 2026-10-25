import logging
import time
from functools import lru_cache

from mem0 import Memory

from app.config import settings

logger = logging.getLogger(__name__)

EMBEDDING_DIMS = 1536


class MemoryServiceError(Exception):
    """Raised when a memory operation the user explicitly asked for fails."""


def build_mem0_config() -> dict:
    return {
        "vector_store": {
            "provider": "pgvector",
            "config": {
                "connection_string": settings.plain_database_url,
                "collection_name": "adaptai_memories",
                "embedding_model_dims": EMBEDDING_DIMS,
            },
        },
        "llm": {
            "provider": "gemini",
            "config": {
                "model": settings.mem0_llm_model or settings.llm_model,
                "api_key": settings.openai_api_key,
                "temperature": 0.1,
            },
        },
        "embedder": {
            "provider": "gemini",
            "config": {
                "model": "models/gemini-embedding-001",
                "embedding_dims": EMBEDDING_DIMS,
                "api_key": settings.openai_api_key,
            },
        },
    }


def _with_retries(fn, attempts: int = 3, base_delay: float = 2.0):
    for attempt in range(attempts):
        try:
            return fn()
        except Exception:
            if attempt == attempts - 1:
                raise
            time.sleep(base_delay * (2**attempt))


def _results(response) -> list[dict]:
    return response.get("results", []) if isinstance(response, dict) else response


class MemoryService:
    """Thin wrapper around Mem0. Background memory work never breaks the chat."""

    def __init__(self, client=None, retry_delay: float = 2.0):
        self._client = client
        self.retry_delay = retry_delay

    @property
    def client(self):
        if self._client is None:
            self._client = Memory.from_config(build_mem0_config())
        return self._client

    def search(self, user_id: str, query: str, limit: int = 5) -> list[str]:
        try:
            response = self.client.search(
                query, filters={"user_id": user_id}, top_k=limit
            )
        except Exception:
            logger.exception("Memory search failed")
            return []
        return [item["memory"] for item in _results(response)]

    def add(self, user_id: str, messages: list[dict]) -> None:
        try:
            _with_retries(
                lambda: self.client.add(messages, user_id=user_id),
                base_delay=self.retry_delay,
            )
        except Exception:
            logger.exception("Memory add failed after retries")

    def list_memories(self, user_id: str) -> list[dict]:
        try:
            response = self.client.get_all(filters={"user_id": user_id})
        except Exception:
            logger.exception("Memory list failed")
            return []
        return [
            {"id": item["id"], "memory": item["memory"]} for item in _results(response)
        ]

    def delete_all(self, user_id: str) -> None:
        try:
            self.client.delete_all(user_id=user_id)
        except Exception as exc:
            logger.exception("Memory delete failed")
            raise MemoryServiceError("Could not delete memories") from exc


@lru_cache
def get_memory_service() -> MemoryService:
    return MemoryService()