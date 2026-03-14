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

    def validate(self):
        if self.LLM_PROVIDER == "gemini" and not self.GEMINI_API_KEY:
            print("⚠️  WARNING: GEMINI_API_KEY is missing. AI features will fail.")
        elif self.LLM_PROVIDER == "groq" and not self.GROQ_API_KEY:
            print("⚠️  WARNING: GROQ_API_KEY is missing. AI features will fail.")
        
        if not self.PINECONE_API_KEY:
            print("⚠️  WARNING: PINECONE_API_KEY is missing. Vector Store features will fail.")
            
settings = Settings()
settings.validate()
