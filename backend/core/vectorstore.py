import chromadb
from chromadb.config import Settings
import os
from backend.core.models import Chunk

class VectorStore:
    def __init__(self):
        self.client = chromadb.PersistentClient(path="chroma_db")
        self.collection = self.client.get_or_create_collection(name="qa_collection")

    def add_chunks(self, chunks: list[Chunk]):
        if not chunks:
            return
            
        ids = [c.id for c in chunks]
        documents = [c.text for c in chunks]
        metadatas = [c.metadata for c in chunks]
        
        self.collection.add(
            ids=ids,
            documents=documents,
            metadatas=metadatas
        )

    def query(self, query: str, top_k: int = 5):
        return self.collection.query(
            query_texts=[query],
            n_results=top_k
        )

    def reset(self):
        self.client.delete_collection("qa_collection")
        self.collection = self.client.get_or_create_collection(name="qa_collection")
