import os
from pathlib import Path
from dotenv import load_dotenv

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent.parent
load_dotenv(BASE_DIR / ".env")

class Settings:
    # Groq LLM Configuration
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    
    # Pinecone Vector Store Configuration
    PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
    PINECONE_INDEX_NAME = os.getenv("PINECONE_INDEX_NAME", "qa-agent-index")
    PINECONE_CLOUD = os.getenv("PINECONE_CLOUD", "aws")  # Options: "aws", "gcp", "azure"
    PINECONE_REGION = os.getenv("PINECONE_REGION", "us-east-1")  # Free tier region

settings = Settings()
