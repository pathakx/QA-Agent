from fastapi import FastAPI
from backend.api import docs_api, agent_api

from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="QA Testing Brain")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(docs_api.router, prefix="/kb", tags=["knowledge-base"])
app.include_router(agent_api.router, prefix="/agent", tags=["agent"])

@app.get("/health")
def health():
    return {"status": "ok"}
