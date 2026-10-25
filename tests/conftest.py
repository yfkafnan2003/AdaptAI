import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db import Base, get_db
from app.main import app
from app.memory import get_memory_service
from app.routes.chat import get_llm


class FakeLLM:
    def __init__(self):
        self.calls = []

    def chat(self, messages):
        self.calls.append(messages)
        return "fake reply"


class FakeMemory:
    def __init__(self):
        self.facts = ["Likes hiking"]
        self.added = []
        self.deleted = []

    def search(self, user_id, query, limit=5):
        return self.facts

    def add(self, user_id, messages):
        self.added.append((user_id, messages))

    def list_memories(self, user_id):
        return [{"id": "m1", "memory": "Likes hiking"}]

    def delete_all(self, user_id):
        self.deleted.append(user_id)


@pytest.fixture
def fake_llm():
    return FakeLLM()


@pytest.fixture
def fake_memory():
    return FakeMemory()


@pytest.fixture
def client(fake_llm, fake_memory):
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
    app.dependency_overrides[get_memory_service] = lambda: fake_memory
    yield TestClient(app)
    app.dependency_overrides.clear()