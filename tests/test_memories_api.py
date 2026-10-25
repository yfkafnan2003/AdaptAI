def test_list_memories(client):
    r = client.get("/users/u1/memories")
    assert r.status_code == 200
    assert r.json() == {
        "user_id": "u1",
        "memories": [{"id": "m1", "memory": "Likes hiking"}],
    }


def test_delete_memories(client, fake_memory):
    r = client.delete("/users/u1/memories")
    assert r.status_code == 204
    assert fake_memory.deleted == ["u1"]