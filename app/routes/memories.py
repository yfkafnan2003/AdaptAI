from fastapi import APIRouter, Depends, Response

from app.memory import MemoryService, get_memory_service

router = APIRouter(prefix="/users/{user_id}/memories", tags=["memories"])


@router.get("")
def list_memories(user_id: str, memory: MemoryService = Depends(get_memory_service)):
    return {"user_id": user_id, "memories": memory.list_memories(user_id)}


@router.delete("", status_code=204)
def delete_memories(user_id: str, memory: MemoryService = Depends(get_memory_service)):
    memory.delete_all(user_id)
    return Response(status_code=204)