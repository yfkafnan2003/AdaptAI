from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import get_db
from app.llm import LLMClient
from app.memory import MemoryService, get_memory_service
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


def build_system_prompt(memories: list[str]) -> str:
    if not memories:
        return SYSTEM_PROMPT
    facts = "\n".join(f"- {m}" for m in memories)
    return (
        f"{SYSTEM_PROMPT}\n\n"
        "Facts remembered about this user from earlier conversations "
        "(use them naturally when relevant, and do not recite them):\n"
        f"{facts}"
    )


def load_history(db: Session, conversation_id: int) -> list[dict]:
    rows = (
        db.query(Message)
        .filter(Message.conversation_id == conversation_id)
        .order_by(Message.id.desc())
        .limit(HISTORY_LIMIT)
        .all()
    )
    rows.reverse()  # oldest first
    return [{"role": m.role, "content": m.content} for m in rows]


@router.post("/chat", response_model=ChatResponse)
def chat(
    req: ChatRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    llm: LLMClient = Depends(get_llm),
    memory: MemoryService = Depends(get_memory_service),
):
    if req.conversation_id is None:
        conversation = Conversation(user_id=req.user_id)
        history: list[dict] = []
    else:
        conversation = db.get(Conversation, req.conversation_id)
        if conversation is None or conversation.user_id != req.user_id:
            raise HTTPException(status_code=404, detail="Conversation not found")
        history = load_history(db, conversation.id)

    memories = memory.search(req.user_id, req.message)
    messages = (
        [{"role": "system", "content": build_system_prompt(memories)}]
        + history
        + [{"role": "user", "content": req.message}]
    )
    reply = llm.chat(messages)

    conversation.messages.append(Message(role="user", content=req.message))
    conversation.messages.append(Message(role="assistant", content=reply))
    db.add(conversation)
    db.commit()

    background_tasks.add_task(
        memory.add,
        req.user_id,
        [
            {"role": "user", "content": req.message},
            {"role": "assistant", "content": reply},
        ],
    )
    return ChatResponse(reply=reply, conversation_id=conversation.id)