from fastapi import FastAPI
from backend.api import docs_api, agent_api
from fastapi.middleware.cors import CORSMiddleware
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="QA Testing Brain")

@app.on_event("startup")
async def startup_event():
    """Log startup information"""
    logger.info("=" * 70)
    logger.info("QA Testing Brain API Starting Up")
    logger.info("=" * 70)
    logger.info("Application is ready to accept connections")
    logger.info("=" * 70)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(docs_api.router, prefix="/kb", tags=["knowledge-base"])
app.include_router(agent_api.router, prefix="/agent", tags=["agent"])

@app.get("/")
def root():
    return {
        "message": "QA Testing Brain API",
        "status": "running",
        "endpoints": {
            "health": "/health",
            "knowledge_base": "/kb",
            "agent": "/agent"
        }
    }

@app.get("/health")
def health():
    return {"status": "ok"}
