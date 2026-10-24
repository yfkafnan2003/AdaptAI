import logging

from app.memory import MemoryService

logging.basicConfig(level=logging.INFO)

svc = MemoryService()
USER = "smoke-test"

svc.client.add(
    [
        {"role": "user", "content": "Hi, my name is Sam and I love hiking on weekends."},
        {"role": "assistant", "content": "Nice to meet you, Sam!"},
    ],
    user_id=USER,
)
print("stored:", svc.client.get_all(filters={"user_id": USER}))
print("search:", svc.search(USER, "What does the user do for fun?"))

svc.client.delete_all(user_id=USER)
print("cleaned up")