from openai import OpenAI
from backend.core.config import settings

class LLMClient:
    def __init__(self):
        # Initialize Groq client using OpenAI-compatible API
        self.client = OpenAI(
            api_key=settings.GROQ_API_KEY,
            base_url="https://api.groq.com/openai/v1"
        )
        self.model_name = "llama-3.3-70b-versatile"
        print(f"✅ Initialized Groq LLM (model: {self.model_name})")

    def generate(self, prompt: str) -> str:
        # Use Groq API (OpenAI-compatible)
        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=[
                {"role": "system", "content": "You are a helpful QA test designer assistant."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=2000
        )
        return response.choices[0].message.content
