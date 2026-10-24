import logging

from mem0 import Memory

from app.config import settings

logger = logging.getLogger(__name__)

EMBEDDING_DIMS = 1536


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
                "model": settings.llm_model,
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


class MemoryService:
    """Thin wrapper around Mem0. Memory failures never break the chat."""

    def __init__(self, client=None):
        self._client = client

    @property
    def client(self):
        if self._client is None:
            self._client = Memory.from_config(build_mem0_config())
        return self._client

    def search(self, user_id: str, query: str, limit: int = 5) -> list[str]:
        try:
            result = self.client.search(
                query, filters={"user_id": user_id}, top_k=limit
            )
        except Exception:
            logger.exception("Memory search failed")
            return []
        items = result.get("results", []) if isinstance(result, dict) else result
        return [item["memory"] for item in items]

    def add(self, user_id: str, messages: list[dict]) -> None:
        try:
            self.client.add(messages, user_id=user_id)
        except Exception:
            logger.exception("Memory add failed")