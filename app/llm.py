from openai import OpenAI
from app.config import settings


class LLMError(Exception):
    """Raised when the LLM provider call fails."""


class LLMClient:
    def __init__(self, client=None):
        self._client = client
        self.model = settings.llm_model

    @property
    def client(self):
        if self._client is None:
            self._client = OpenAI(
                api_key=settings.openai_api_key,
                base_url=settings.openai_base_url,
            )
        return self._client

    def chat(self, messages: list[dict]) -> str:
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
            )
        except Exception as exc:
            raise LLMError(f"LLM request failed: {exc}") from exc
        return response.choices[0].message.content or ""