from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app import models  
from app.config import settings
from app.db import Base, engine
from app.llm import LLMError
from app.routes import chat


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title=settings.app_name, lifespan=lifespan)
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