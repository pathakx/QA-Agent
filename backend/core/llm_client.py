import google.generativeai as genai
from openai import OpenAI
from backend.core.config import settings

class LLMClient:
    def __init__(self):
        self.provider = settings.LLM_PROVIDER.lower()
        
        if self.provider == "groq":
            # Initialize Groq client using OpenAI-compatible API
            self.client = OpenAI(
                api_key=settings.GROQ_API_KEY,
                base_url="https://api.groq.com/openai/v1"
            )
            self.model_name = "llama-3.3-70b-versatile"
            print(f"✅ Initialized Groq LLM (model: {self.model_name})")
        elif self.provider == "gemini":
            # Initialize Gemini client
            genai.configure(api_key=settings.GEMINI_API_KEY)
            self.model = genai.GenerativeModel("gemini-2.5-flash")
            print(f"✅ Initialized Gemini LLM (model: gemini-2.5-flash)")
        else:
            raise ValueError(f"Unsupported LLM provider: {self.provider}. Use 'gemini' or 'groq'")

    def generate(self, prompt: str) -> str:
        if self.provider == "groq":
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
        elif self.provider == "gemini":
            # Use Gemini API
            response = self.model.generate_content(prompt)
            return response.text

