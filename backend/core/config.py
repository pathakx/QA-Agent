import os
from pathlib import Path
from dotenv import load_dotenv

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent.parent
load_dotenv(BASE_DIR / ".env")

class Settings:
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    LLM_PROVIDER = os.getenv("LLM_PROVIDER", "gemini")  # Options: "gemini", "groq"
    PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
    PINECONE_INDEX_NAME = os.getenv("PINECONE_INDEX_NAME", "qa-agent-index")

    # ── Migration Settings (Phase 1) ──────────────────────────
    # Browser engine: "selenium" (default, safe) or "playwright"
    BROWSER_ENGINE = os.getenv("BROWSER_ENGINE", "selenium")
    # Master kill switch — must be "true" for any Playwright behavior
    PLAYWRIGHT_ENABLED = os.getenv("PLAYWRIGHT_ENABLED", "false").lower() in ("true", "1", "yes")
    # Canary rollout percentage (0-100). Only applies when PLAYWRIGHT_ENABLED=true.
    PLAYWRIGHT_ROLLOUT_PCT = int(os.getenv("PLAYWRIGHT_ROLLOUT_PCT", "0"))
    # Playwright feature sub-flags
    PLAYWRIGHT_VIDEO = os.getenv("PLAYWRIGHT_VIDEO", "false").lower() in ("true", "1", "yes")
    PLAYWRIGHT_TRACING = os.getenv("PLAYWRIGHT_TRACING", "false").lower() in ("true", "1", "yes")

    def validate(self):
        if self.LLM_PROVIDER == "gemini" and not self.GEMINI_API_KEY:
            print("⚠️  WARNING: GEMINI_API_KEY is missing. AI features will fail.")
        elif self.LLM_PROVIDER == "groq" and not self.GROQ_API_KEY:
            print("⚠️  WARNING: GROQ_API_KEY is missing. AI features will fail.")
        
        if not self.PINECONE_API_KEY:
            print("⚠️  WARNING: PINECONE_API_KEY is missing. Vector Store features will fail.")

        # Migration validation
        if self.PLAYWRIGHT_ENABLED:
            print(f"[MIGRATION] Playwright ENABLED (engine={self.BROWSER_ENGINE}, rollout={self.PLAYWRIGHT_ROLLOUT_PCT}%)")
        else:
            print(f"[MIGRATION] Playwright DISABLED (engine={self.BROWSER_ENGINE})")
            
settings = Settings()
settings.validate()
