from fastapi import APIRouter, Depends

from app.llm import LLMClient
from app.schemas import ChatRequest, ChatResponse

router = APIRouter()

SYSTEM_PROMPT = (
    "You are AdaptAI, a helpful assistant that adapts to the user. "
    "Be clear and concise."
)


def get_llm() -> LLMClient:
    return LLMClient()


@router.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest, llm: LLMClient = Depends(get_llm)):
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": req.message},
    ]
    return ChatResponse(reply=llm.chat(messages))