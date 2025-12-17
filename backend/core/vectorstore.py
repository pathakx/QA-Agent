import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions
import os
import shutil
from backend.core.models import Chunk

from backend.core.config import settings

class VectorStore:
    def __init__(self):
        self.client = chromadb.PersistentClient(path=settings.VECTOR_DB_DIR)
        # Use default local embedding function (sentence-transformers)
        # Note: Using local embeddings to avoid API quota limits
        self.embedding_function = embedding_functions.DefaultEmbeddingFunction()
        
        # Try to get or create collection, handle embedding function conflicts
        try:
            self.collection = self.client.get_or_create_collection(
                name="qa_collection",
                embedding_function=self.embedding_function
            )
        except ValueError as e:
            # If embedding function conflict, delete and recreate with new embedding function
            if "embedding function conflict" in str(e).lower():
                print(f"Embedding function conflict detected. Recreating collection with new embedding function...")
                self.client.delete_collection("qa_collection")
                self.collection = self.client.create_collection(
                    name="qa_collection",
                    embedding_function=self.embedding_function
                )
            else:
                raise

    def add_chunks(self, chunks: list[Chunk]):
        if not chunks:
            print("Warning: add_chunks called with empty chunks list")
            return
            
        ids = [c.id for c in chunks]
        documents = [c.text for c in chunks]
        metadatas = [c.metadata for c in chunks]
        
        print(f"Adding {len(chunks)} chunks to vector store")
        self.collection.add(
            ids=ids,
            documents=documents,
            metadatas=metadatas
        )
        print(f"Successfully added chunks. Total count now: {self.collection.count()}")

    def query(self, query: str, top_k: int = 5):
        try:
            # Check if collection is empty first
            if self.collection.count() == 0:
                print("Warning: Collection is empty, returning no results")
                return {"ids": [[]], "documents": [[]], "metadatas": [[]], "distances": [[]]}
            
            return self.collection.query(
                query_texts=[query],
                n_results=top_k
            )
        except Exception as e:
            print(f"Error querying collection: {e}")
            # Return empty results structure instead of crashing
            return {"ids": [[]], "documents": [[]], "metadatas": [[]], "distances": [[]]}

    def reset(self):
        """Completely reset the vector store by deleting all data and reinitializing."""
        import time
        import gc
        
        print("Starting vector store reset...")
        
        try:
            # Delete the collection if it exists
            try:
                self.client.delete_collection("qa_collection")
                print("Deleted existing collection")
            except Exception as e:
                print(f"No existing collection to delete: {e}")
            
            # Close the client connection and clear references
            try:
                del self.collection
                del self.client
                print("Closed client connections")
            except Exception as e:
                print(f"Error closing connections: {e}")
            
            # Force garbage collection to release file handles (important on Windows)
            gc.collect()
            time.sleep(0.5)  # Give OS time to release file locks
            
            # Physically delete the ChromaDB directory to ensure clean state
            if os.path.exists(settings.VECTOR_DB_DIR):
                print(f"Removing ChromaDB directory: {settings.VECTOR_DB_DIR}")
                try:
                    shutil.rmtree(settings.VECTOR_DB_DIR)
                    print("ChromaDB directory removed")
                except PermissionError as e:
                    print(f"Warning: Could not delete some files (may be locked): {e}")
                    print("Attempting to delete individual files...")
                    # Try to delete what we can
                    for root, dirs, files in os.walk(settings.VECTOR_DB_DIR, topdown=False):
                        for name in files:
                            try:
                                os.remove(os.path.join(root, name))
                            except Exception:
                                pass
                        for name in dirs:
                            try:
                                os.rmdir(os.path.join(root, name))
                            except Exception:
                                pass
            
            # Reinitialize everything from scratch
            print("Reinitializing ChromaDB client...")
            self.client = chromadb.PersistentClient(path=settings.VECTOR_DB_DIR)
            self.embedding_function = embedding_functions.DefaultEmbeddingFunction()
            self.collection = self.client.create_collection(
                name="qa_collection",
                embedding_function=self.embedding_function
            )
            
            print(f"Vector store reset complete. Collection count: {self.collection.count()}")
        except Exception as e:
            print(f"Error during reset: {e}")
            import traceback
            traceback.print_exc()
            raise
    
    def count(self):
        """Return the number of embeddings in the collection."""
        try:
            return self.collection.count()
        except Exception as e:
            print(f"Error getting count: {e}")
            return 0
