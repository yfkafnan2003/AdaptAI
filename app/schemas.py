from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    user_id: str = Field(min_length=1, max_length=100)
    message: str = Field(min_length=1, max_length=4000)
    conversation_id: int | None = None


class ChatResponse(BaseModel):
    reply: str
    conversation_id: int