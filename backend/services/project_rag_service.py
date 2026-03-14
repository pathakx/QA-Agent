"""
Project-aware RAG service for retrieving context from project-specific knowledge bases
"""
from backend.core.models import Chunk
from backend.core.vectorstore import VectorStore

def retrieve_project_context(query: str, vector_store: VectorStore, top_k=8) -> list[Chunk]:
    """Retrieve context from a project-specific vector store"""
    results = vector_store.query(query, top_k)
    chunks = []
    
    # Check if results exist and have documents
    if results and "documents" in results and results["documents"]:
        # results["documents"] is a list of lists (one list per query)
        # We only queried one text, so we take the first list
        for i in range(len(results["documents"][0])):
            chunks.append(
                Chunk(
                    id=results["ids"][0][i],
                    doc_id="unknown",  # metadata can be expanded later
                    text=results["documents"][0][i],
                    metadata=results["metadatas"][0][i]
                )
            )
    return chunks

def build_testcase_prompt(query: str, chunks: list[Chunk], existing_testcases: list = None) -> str:
    """Build test case generation prompt with context chunks"""
    context_str = "\n".join(
        [f"[CHUNK {c.metadata.get('chunk_index')}] {c.text}" for c in chunks]
    )
    
    existing_str = ""
    if existing_testcases:
        existing_str = "\nEXISTING TEST CASES (DO NOT DUPLICATE SCENARIOS):\n"
        for tc in existing_testcases:
            existing_str += f"- {tc.get('test_id')}: {tc.get('scenario')}\n"
        existing_str += "\nINSTRUCTION: If a scenario above already exists, DO NOT generate it again unless you are updating it with new details. Focus on new scenarios.\n"

    schema = """
Output MUST be a JSON array.
Each object MUST contain:

- test_id (Use consistent naming convention like TC-FEATURE-001)
- feature
- scenario
- preconditions
- steps (List of strings)
- test_data
- expected_result
- grounded_in (array of document or chunk references)
"""

    return f"""
SYSTEM:
You are a QA test designer. You MUST base all test cases ONLY on the provided context.
If something is not specified, respond "Not defined in provided documentation".
Output MUST be valid JSON.

{existing_str}

CONTEXT:
{context_str}

USER REQUEST:
{query}
If the user asks for "ALL" test cases, generate comprehensive coverage but skip scenarios that are already listed above in EXISTING TEST CASES.

REQUIRED OUTPUT FORMAT:
{schema}
"""
