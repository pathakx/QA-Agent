import json
from backend.services.rag_service import retrieve_context, build_testcase_prompt
from backend.core.llm_client import LLMClient

llm = LLMClient()

def generate_testcases(query: str):
    chunks = retrieve_context(query)
    prompt = build_testcase_prompt(query, chunks)
    response = llm.generate(prompt)

    try:
        parsed = json.loads(response)
    except json.JSONDecodeError:
        # Attempt to clean up markdown code blocks if present
        clean_response = response.strip()
        if clean_response.startswith("```json"):
            clean_response = clean_response[7:]
        if clean_response.endswith("```"):
            clean_response = clean_response[:-3]
        
        try:
            parsed = json.loads(clean_response)
        except json.JSONDecodeError:
            parsed = {"error": "Invalid JSON from model", "raw": response}

    return {
        "testcases": parsed,
        "raw_context": [c.text for c in chunks]
    }
