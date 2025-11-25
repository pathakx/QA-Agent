from fastapi import FastAPI
from backend.api import docs_api, agent_api

app = FastAPI(title="QA Testing Brain")

app.include_router(docs_api.router, prefix="/kb", tags=["knowledge-base"])
app.include_router(agent_api.router, prefix="/agent", tags=["agent"])

@app.get("/health")
def health():
    return {"status": "ok"}
