from backend.core.models import Chunk
from backend.services.kb_service import get_vector_store

def retrieve_context(query: str, top_k=8) -> list[Chunk]:
    # Get the current vector store instance
    vector_store = get_vector_store()
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

def build_testcase_prompt(query: str, chunks: list[Chunk]) -> str:
    context_str = "\n".join(
        [f"[CHUNK {c.metadata.get('chunk_index')}] {c.text}" for c in chunks]
    )

    schema = """
Output MUST be a JSON array.
Each object MUST contain:

- test_id
- feature
- scenario
- preconditions
- steps
- test_data
- expected_result
- grounded_in (array of document or chunk references)
"""

    return f"""
SYSTEM:
You are a QA test designer. You MUST base all test cases ONLY on the provided context.
If something is not specified, respond "Not defined in provided documentation".
Output MUST be valid JSON.

CONTEXT:
{context_str}

USER REQUEST:
{query}

REQUIRED OUTPUT FORMAT:
{schema}
"""
