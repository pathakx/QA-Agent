from backend.core.models import Chunk
import uuid

def chunk_text(doc_id: str, text: str, chunk_size=700, overlap=120):
    chunks = []
    start = 0
    index = 0

    while start < len(text):
        end = start + chunk_size
        chunk_text = text[start:end]
        
        chunks.append(
            Chunk(
                id=str(uuid.uuid4()),
                doc_id=doc_id,
                text=chunk_text,
                metadata={"chunk_index": index}
            )
        )
        
        start = end - overlap
        index += 1

    return chunks
