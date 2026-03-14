import os
import time
from backend.core.models import Chunk
from backend.core.config import settings
from sentence_transformers import SentenceTransformer
from pinecone import Pinecone
from transformers import logging as transformers_logging

# Suppress warnings from transformers (like "position_ids unexpected")
transformers_logging.set_verbosity_error()

class VectorStore:
    def __init__(self, collection_name: str = "qa_collection"):
        """
        Initialize Pinecone Vector Store.
        collection_name is used as a fallback if PINECONE_INDEX_NAME is not set, 
        or simply ignored if we enforce the env var.
        """
        self.api_key = settings.PINECONE_API_KEY
        self.index_name = settings.PINECONE_INDEX_NAME

        if not self.api_key:
            print("Error: PINECONE_API_KEY not found in settings.")
            raise ValueError("PINECONE_API_KEY not set.")
        
        if not self.index_name:
             print(f"Warning: PINECONE_INDEX_NAME not set. Using provided collection_name: {collection_name}")
             self.index_name = collection_name

        # Initialize Pinecone
        self.pc = Pinecone(api_key=self.api_key)
        
        # Connect to the index
        print(f"Connecting to Pinecone index: {self.index_name}")
        self.index = self.pc.Index(self.index_name)
        
        # Initialize Embedding Model
        # This matches the dimension of the index (384)
        print("Loading embedding model: sentence-transformers/all-MiniLM-L6-v2...")
        self.model = SentenceTransformer('all-MiniLM-L6-v2') 
        print("Embedding model loaded.")

    def add_chunks(self, chunks: list[Chunk]):
        if not chunks:
            print("Warning: add_chunks called with empty chunks list")
            return
            
        print(f"Processing {len(chunks)} chunks for Pinecone...")
        
        # Generate embeddings
        texts = [c.text for c in chunks]
        embeddings = self.model.encode(texts)
        
        vectors = []
        for i, chunk in enumerate(chunks):
            # Prepare metadata
            metadata = chunk.metadata.copy()
            # Ensure text is stored in metadata for retrieval
            if 'text' not in metadata:
                metadata['text'] = chunk.text
            
            # Pinecone expects 'values' as the embedding vector
            vectors.append({
                "id": chunk.id,
                "values": embeddings[i].tolist(),
                "metadata": metadata
            })
        
        # Upsert to Pinecone
        # Determine batch size (Pinecone recommendation is usually <1000, keep it safe at 100)
        batch_size = 100
        total_vectors = len(vectors)
        
        print(f"Upserting {total_vectors} vectors to Pinecone...")
        for i in range(0, total_vectors, batch_size):
            batch = vectors[i:i+batch_size]
            self.index.upsert(vectors=batch)
            print(f"Upserted batch {i} to {min(i+batch_size, total_vectors)}")
            
        print(f"Successfully added chunks. Total count now: {self.count()}")

    def delete_document(self, filename: str):
        """Delete all vectors associated with a specific filename."""
        try:
            print(f"Deleting vectors for document: {filename}")
            # Pinecone delete by metadata filter
            self.index.delete(filter={"filename": filename})
            print(f"Successfully deleted vectors for {filename}")
        except Exception as e:
            print(f"Error deleting document {filename}: {e}")

    def query(self, query: str, top_k: int = 5):
        try:
            # Check if index has vectors? Pinecone check is expensive, maybe just query.
            if self.count() == 0:
                print("Warning: Index is empty, returning no results")
                return {"ids": [[]], "documents": [[]], "metadatas": [[]], "distances": [[]]}

            # Generate query embedding
            query_vector = self.model.encode(query).tolist()
            
            # Query Pinecone
            results = self.index.query(
                vector=query_vector,
                top_k=top_k,
                include_metadata=True
            )
            
            # Formatting results to match old Chroma interface:
            # {'ids': [[id1, id2]], 'documents': [[text1, text2]], ...}
            ids = []
            documents = []
            metadatas = []
            distances = []
            
            for match in results.matches:
                ids.append(match.id)
                documents.append(match.metadata.get('text', ''))
                metadatas.append(match.metadata)
                distances.append(match.score)
                
            return {
                "ids": [ids],
                "documents": [documents],
                "metadatas": [metadatas],
                "distances": [distances]
            }
        except Exception as e:
            print(f"Error querying index: {e}")
            # Return empty structure on error
            return {"ids": [[]], "documents": [[]], "metadatas": [[]], "distances": [[]]}

    def reset(self):
        """Delete all vectors in the index."""
        try:
            print(f"Resetting index '{self.index_name}'...")
            self.index.delete(delete_all=True)
            print("Index reset successful.")
        except Exception as e:
            print(f"Error during reset: {e}")
            raise
    
    def count(self):
        """Return the number of vectors in the index."""
        try:
            stats = self.index.describe_index_stats()
            return stats.total_vector_count
        except Exception as e:
            print(f"Error getting count: {e}")
            return 0
