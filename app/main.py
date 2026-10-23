from fastapi import FastAPI

app = FastAPI(title="AdaptAI")


@app.get("/health")
def health():
    return {"status": "ok"}