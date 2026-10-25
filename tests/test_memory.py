import pytest

from app.memory import MemoryService, MemoryServiceError


class FakeMem0:
    def __init__(self):
        self.added = []
        self.deleted = []
        self.search_calls = []

    def search(self, query, filters, top_k=5):
        self.search_calls.append((query, filters, top_k))
        return {"results": [{"memory": "Loves hiking"}, {"memory": "Name is Sam"}]}

    def add(self, messages, user_id):
        self.added.append((user_id, messages))

    def get_all(self, filters):
        return {"results": [{"id": "m1", "memory": "Loves hiking", "score": None}]}

    def delete_all(self, user_id):
        self.deleted.append(user_id)


class BrokenMem0:
    def search(self, *args, **kwargs):
        raise RuntimeError("down")

    def add(self, *args, **kwargs):
        raise RuntimeError("down")

    def get_all(self, *args, **kwargs):
        raise RuntimeError("down")

    def delete_all(self, *args, **kwargs):
        raise RuntimeError("down")


class FlakyMem0:
    def __init__(self):
        self.calls = 0

    def add(self, messages, user_id):
        self.calls += 1
        if self.calls < 2:
            raise RuntimeError("503")


def test_search_returns_memory_strings_scoped_to_user():
    fake = FakeMem0()
    svc = MemoryService(client=fake)
    assert svc.search("u1", "hobbies") == ["Loves hiking", "Name is Sam"]
    assert fake.search_calls == [("hobbies", {"user_id": "u1"}, 5)]


def test_add_forwards_to_client():
    fake = FakeMem0()
    svc = MemoryService(client=fake)
    svc.add("u1", [{"role": "user", "content": "hi"}])
    assert fake.added == [("u1", [{"role": "user", "content": "hi"}])]


def test_search_failure_returns_empty_list():
    svc = MemoryService(client=BrokenMem0())
    assert svc.search("u1", "anything") == []


def test_add_failure_does_not_raise():
    svc = MemoryService(client=BrokenMem0(), retry_delay=0)
    svc.add("u1", [{"role": "user", "content": "hi"}])


def test_add_retries_transient_errors():
    flaky = FlakyMem0()
    svc = MemoryService(client=flaky, retry_delay=0)
    svc.add("u1", [{"role": "user", "content": "hi"}])
    assert flaky.calls == 2


def test_list_memories_maps_results():
    svc = MemoryService(client=FakeMem0())
    assert svc.list_memories("u1") == [{"id": "m1", "memory": "Loves hiking"}]


def test_list_memories_failure_returns_empty_list():
    svc = MemoryService(client=BrokenMem0())
    assert svc.list_memories("u1") == []


def test_delete_all_forwards_to_client():
    fake = FakeMem0()
    MemoryService(client=fake).delete_all("u1")
    assert fake.deleted == ["u1"]


def test_delete_all_failure_raises():
    with pytest.raises(MemoryServiceError):
        MemoryService(client=BrokenMem0()).delete_all("u1")