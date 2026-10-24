from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import get_db
from app.llm import LLMClient
from app.models import Conversation, Message
from app.schemas import ChatRequest, ChatResponse

router = APIRouter()

SYSTEM_PROMPT = (
    "You are AdaptAI, a helpful assistant that adapts to the user. "
    "Be clear and concise."
)
HISTORY_LIMIT = 20


def get_llm() -> LLMClient:
    return LLMClient()


def load_history(db: Session, conversation_id: int) -> list[dict]:
    rows = (
        db.query(Message)
        .filter(Message.conversation_id == conversation_id)
        .order_by(Message.id.desc())
        .limit(HISTORY_LIMIT)
        .all()
    )
    rows.reverse()  
    return [{"role": m.role, "content": m.content} for m in rows]


@router.post("/chat", response_model=ChatResponse)
def chat(
    req: ChatRequest,
    db: Session = Depends(get_db),
    llm: LLMClient = Depends(get_llm),
):
    if req.conversation_id is None:
        conversation = Conversation(user_id=req.user_id)
        history: list[dict] = []
    else:
        conversation = db.get(Conversation, req.conversation_id)
        if conversation is None or conversation.user_id != req.user_id:
            raise HTTPException(status_code=404, detail="Conversation not found")
        history = load_history(db, conversation.id)

    messages = (
        [{"role": "system", "content": SYSTEM_PROMPT}]
        + history
        + [{"role": "user", "content": req.message}]
    )
    reply = llm.chat(messages)

    conversation.messages.append(Message(role="user", content=req.message))
    conversation.messages.append(Message(role="assistant", content=reply))
    db.add(conversation)
    db.commit()

    return ChatResponse(reply=reply, conversation_id=conversation.id)