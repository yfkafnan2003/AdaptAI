from app.memory import MemoryService


class FakeMem0:
    def __init__(self):
        self.added = []
        self.search_calls = []

    def search(self, query, filters, top_k=5):
        self.search_calls.append((query, filters, top_k))
        return {"results": [{"memory": "Loves hiking"}, {"memory": "Name is Sam"}]}

    def add(self, messages, user_id):
        self.added.append((user_id, messages))


def test_search_returns_memory_strings_scoped_to_user():
    fake = FakeMem0()
    svc = MemoryService(client=fake)
    assert svc.search("u1", "hobbies") == ["Loves hiking", "Name is Sam"]
    assert fake.search_calls == [("hobbies", {"user_id": "u1"}, 5)]

class BrokenMem0:
    def search(self, *args, **kwargs):
        raise RuntimeError("down")

    def add(self, *args, **kwargs):
        raise RuntimeError("down")


def test_search_returns_memory_strings():
    svc = MemoryService(client=FakeMem0())
    assert svc.search("u1", "hobbies") == ["Loves hiking", "Name is Sam"]


def test_add_forwards_to_client():
    fake = FakeMem0()
    svc = MemoryService(client=fake)
    svc.add("u1", [{"role": "user", "content": "hi"}])
    assert fake.added == [("u1", [{"role": "user", "content": "hi"}])]


def test_search_failure_returns_empty_list():
    svc = MemoryService(client=BrokenMem0())
    assert svc.search("u1", "anything") == []


def test_add_failure_does_not_raise():
    svc = MemoryService(client=BrokenMem0())
    svc.add("u1", [{"role": "user", "content": "hi"}])