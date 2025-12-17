import json
from backend.services.rag_service import retrieve_context, build_testcase_prompt
from backend.core.llm_client import LLMClient

llm = LLMClient()

def generate_testcases(query: str):
    try:
        print(f"Generating test cases for query: {query}")
        chunks = retrieve_context(query)
        print(f"Retrieved {len(chunks)} context chunks")
        
        # Check if knowledge base is empty
        if not chunks or len(chunks) == 0:
            return {
                "testcases": [],
                "error": "Knowledge Base is empty. Please upload documents first in the Knowledge Base tab.",
                "empty_kb": True
            }
        
        prompt = build_testcase_prompt(query, chunks)
        print("Sending prompt to LLM...")
        response = llm.generate(prompt)
        print(f"Received response from LLM (length: {len(response)})")

        # Try to parse JSON response
        try:
            parsed = json.loads(response)
            print("Successfully parsed JSON on first attempt")
        except json.JSONDecodeError as e:
            print(f"JSON parse error: {e}")
            # Attempt to clean up markdown code blocks if present
            clean_response = response.strip()
            if clean_response.startswith("```json"):
                clean_response = clean_response[7:]
                print("Removed ```json prefix")
            elif clean_response.startswith("```"):
                clean_response = clean_response[3:]
                print("Removed ``` prefix")
            
            if clean_response.endswith("```"):
                clean_response = clean_response[:-3]
                print("Removed ``` suffix")
            
            try:
                parsed = json.loads(clean_response.strip())
                print("Successfully parsed JSON after cleaning")
            except json.JSONDecodeError as e2:
                print(f"JSON parse failed even after cleaning: {e2}")
                print(f"Response preview: {response[:200]}...")
                return {
                    "testcases": [],
                    "error": "Invalid JSON from model",
                    "raw_response": response[:500],
                    "parse_error": str(e2)
                }
        
        # Ensure parsed is in the correct format
        # LLM should return an array of test cases
        if isinstance(parsed, list):
            testcases = parsed
            print(f"Parsed {len(testcases)} test cases")
        elif isinstance(parsed, dict) and "testcases" in parsed:
            testcases = parsed["testcases"]
            print(f"Extracted {len(testcases)} test cases from dict")
        else:
            print(f"Unexpected response structure: {type(parsed)}")
            testcases = [parsed] if parsed else []

        return {
            "testcases": testcases,
            "raw_context": [c.text[:100] for c in chunks]  # Truncate for size
        }
    except Exception as e:
        print(f"ERROR in generate_testcases: {str(e)}")
        import traceback
        traceback.print_exc()
        
        # Log to file as well
        try:
            with open("backend_error.log", "a") as f:
                f.write(f"ERROR: {str(e)}\n")
                f.write(traceback.format_exc())
                f.write("\n" + "="*50 + "\n")
        except:
            pass
        
        raise e
