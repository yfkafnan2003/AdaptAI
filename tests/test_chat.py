from app.llm import LLMError
from app.main import app
from app.routes.chat import get_llm


class BrokenLLM:
    def chat(self, messages):
        raise LLMError("boom")


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


def test_llm_failure_returns_502_and_stores_no_memory(client, fake_memory):
    app.dependency_overrides[get_llm] = lambda: BrokenLLM()
    r = client.post("/chat", json={"user_id": "u1", "message": "hi"})
    assert r.status_code == 502
    assert fake_memory.added == []


def test_memories_are_added_to_system_prompt(client, fake_llm):
    client.post("/chat", json={"user_id": "u1", "message": "plan my weekend"})
    system = fake_llm.calls[0][0]
    assert system["role"] == "system"
    assert "Likes hiking" in system["content"]


def test_no_memories_uses_plain_system_prompt(client, fake_llm, fake_memory):
    fake_memory.facts = []
    client.post("/chat", json={"user_id": "u1", "message": "hi"})
    assert "Facts remembered" not in fake_llm.calls[0][0]["content"]


def test_exchange_is_saved_to_memory_after_reply(client, fake_memory):
    client.post("/chat", json={"user_id": "u1", "message": "I love tea"})
    assert fake_memory.added == [
        (
            "u1",
            [
                {"role": "user", "content": "I love tea"},
                {"role": "assistant", "content": "fake reply"},
            ],
        )
    ]