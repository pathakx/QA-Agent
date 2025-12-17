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
    VECTOR_DB_DIR = os.getenv("VECTOR_DB_DIR", "chroma_db")

settings = Settings()
