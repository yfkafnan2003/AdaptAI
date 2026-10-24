import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db import Base, get_db
from app.llm import LLMError
from app.main import app
from app.routes.chat import get_llm


class FakeLLM:
    def __init__(self):
        self.calls = []

    def chat(self, messages):
        self.calls.append(messages)
        return "fake reply"


class BrokenLLM:
    def chat(self, messages):
        raise LLMError("boom")


@pytest.fixture
def fake_llm():
    return FakeLLM()


@pytest.fixture
def client(fake_llm):
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    TestingSession = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)

    def override_db():
        db = TestingSession()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_llm] = lambda: fake_llm
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_new_chat_returns_reply_and_conversation_id(client):
    r = client.post("/chat", json={"user_id": "u1", "message": "hi"})
    assert r.status_code == 200
    assert r.json()["reply"] == "fake reply"
    assert isinstance(r.json()["conversation_id"], int)


def test_follow_up_includes_previous_messages(client, fake_llm):
    first = client.post("/chat", json={"user_id": "u1", "message": "my name is Sam"})
    cid = first.json()["conversation_id"]

    client.post(
        "/chat",
        json={"user_id": "u1", "conversation_id": cid, "message": "what is my name?"},
    )

    sent = fake_llm.calls[1]
    contents = [m["content"] for m in sent]
    assert "my name is Sam" in contents
    assert "fake reply" in contents
    assert sent[-1] == {"role": "user", "content": "what is my name?"}


def test_other_user_cannot_use_conversation(client):
    first = client.post("/chat", json={"user_id": "u1", "message": "hi"})
    cid = first.json()["conversation_id"]

    r = client.post(
        "/chat", json={"user_id": "u2", "conversation_id": cid, "message": "hi"}
    )
    assert r.status_code == 404


def test_unknown_conversation_returns_404(client):
    r = client.post(
        "/chat", json={"user_id": "u1", "conversation_id": 999, "message": "hi"}
    )
    assert r.status_code == 404


def test_empty_message_rejected(client):
    r = client.post("/chat", json={"user_id": "u1", "message": ""})
    assert r.status_code == 422


def test_llm_failure_returns_502(client):
    app.dependency_overrides[get_llm] = lambda: BrokenLLM()
    r = client.post("/chat", json={"user_id": "u1", "message": "hi"})
    assert r.status_code == 502