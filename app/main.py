from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.config import settings
from app.llm import LLMError
from app.routes import chat

app = FastAPI(title=settings.app_name)
app.include_router(chat.router)


@app.exception_handler(LLMError)
async def llm_error_handler(request: Request, exc: LLMError):
    return JSONResponse(
        status_code=502,
        content={"detail": "The AI provider failed to respond. Please try again."},
    )


@app.get("/health")
def health():
    return {"status": "ok"}