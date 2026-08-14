from openai import OpenAI
from backend.core.config import settings

class LLMClient:
    def __init__(self):
        self.provider = settings.LLM_PROVIDER.lower()
        import time
        self.last_request_time = 0
        if self.provider == "groq":
            # Initialize Groq client using OpenAI-compatible API
            self.min_interval = 60.0 / 20.0  # Conservative rate limit (20 RPM)
            self.client = OpenAI(
                api_key=settings.GROQ_API_KEY,
                base_url="https://api.groq.com/openai/v1"
            )
            self.model_name = "llama-3.3-70b-versatile"
            print(f"[OK] Initialized Groq LLM (model: {self.model_name})")
        else:
            raise ValueError(f"Unsupported LLM provider: {self.provider}. Only 'groq' is supported.")

    def _wait_for_rate_limit(self):
        import time
        current_time = time.time()
        elapsed = current_time - self.last_request_time
        if elapsed < self.min_interval:
            sleep_time = self.min_interval - elapsed
            print(f"Rate limiting: Sleeping for {sleep_time:.2f}s")
            time.sleep(sleep_time)
        self.last_request_time = time.time()

    def generate(self, prompt: str) -> str:
        self._wait_for_rate_limit()
        max_retries = 5
        base_delay = 2
        
        for attempt in range(max_retries):
            try:
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
            except Exception as e:
                import time
                import random
                
                error_msg = str(e).lower()
                is_rate_limit = "429" in error_msg or "resourceexhausted" in error_msg or "quota" in error_msg
                
                if is_rate_limit and attempt < max_retries - 1:
                    sleep_time = (base_delay * (2 ** attempt)) + random.uniform(0, 1)
                    print(f"Rate limit hit ({error_msg[:50]}...). Retrying in {sleep_time:.2f}s...")
                    time.sleep(sleep_time)
                else:
                    raise e
        return ""

