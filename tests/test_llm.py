from types import SimpleNamespace

import pytest

from app.llm import LLMClient, LLMError


def make_fake_client(content="Hello!", error=None):
    def create(**kwargs):
        if error:
            raise error
        message = SimpleNamespace(content=content)
        return SimpleNamespace(choices=[SimpleNamespace(message=message)])

    completions = SimpleNamespace(create=create)
    return SimpleNamespace(chat=SimpleNamespace(completions=completions))


def test_chat_returns_text():
    llm = LLMClient(client=make_fake_client("Hi there"))
    assert llm.chat([{"role": "user", "content": "hello"}]) == "Hi there"


def test_chat_wraps_provider_errors():
    llm = LLMClient(client=make_fake_client(error=RuntimeError("boom")))
    with pytest.raises(LLMError):
        llm.chat([{"role": "user", "content": "hello"}])