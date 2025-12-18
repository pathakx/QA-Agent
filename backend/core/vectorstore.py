from pinecone import Pinecone, ServerlessSpec
from sentence_transformers import SentenceTransformer
import os
import time
from backend.core.models import Chunk
from backend.core.config import settings

class PineconeVectorStore:
    def __init__(self):
        """Initialize Pinecone vector store with sentence-transformers embeddings."""
        try:
            print("Initializing Pinecone vector store...")
            
            # Initialize Pinecone
            print(f"Connecting to Pinecone with API key: {settings.PINECONE_API_KEY[:10]}...")
            self.pc = Pinecone(api_key=settings.PINECONE_API_KEY)
            print("✓ Connected to Pinecone")
            
            # Initialize embedding model (same as ChromaDB default)
            print("Loading embedding model 'all-MiniLM-L6-v2'...")
            self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
            self.embedding_dimension = 384  # Dimension for all-MiniLM-L6-v2
            print("✓ Embedding model loaded")
            
            # Index configuration
            self.index_name = settings.PINECONE_INDEX_NAME
            self.namespace = "qa-agent"
            
            # Create index if it doesn't exist
            self._ensure_index_exists()
            
            # Connect to index
            self.index = self.pc.Index(self.index_name)
            print(f"✓ Connected to Pinecone index: {self.index_name}")
        except Exception as e:
            print(f"❌ ERROR initializing Pinecone vector store: {e}")
            import traceback
            traceback.print_exc()
            raise
    
    def _ensure_index_exists(self):
        """Create Pinecone index if it doesn't exist."""
        existing_indexes = [index.name for index in self.pc.list_indexes()]
        
        if self.index_name not in existing_indexes:
            print(f"Creating new Pinecone index: {self.index_name}")
            self.pc.create_index(
                name=self.index_name,
                dimension=self.embedding_dimension,
                metric='cosine',
                spec=ServerlessSpec(
                    cloud=settings.PINECONE_CLOUD,
                    region=settings.PINECONE_REGION
                )
            )
            # Wait for index to be ready
            while not self.pc.describe_index(self.index_name).status['ready']:
                print("Waiting for index to be ready...")
                time.sleep(1)
            print(f"Index {self.index_name} created successfully")
        else:
            print(f"Using existing Pinecone index: {self.index_name}")
    
    def _generate_embeddings(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for a list of texts."""
        embeddings = self.embedding_model.encode(texts, show_progress_bar=False)
        return embeddings.tolist()
    
    def add_chunks(self, chunks: list[Chunk]):
        """Add chunks to Pinecone index."""
        if not chunks:
            print("Warning: add_chunks called with empty chunks list")
            return
        
        print(f"Adding {len(chunks)} chunks to Pinecone")
        
        # Prepare data for upsert
        texts = [c.text for c in chunks]
        embeddings = self._generate_embeddings(texts)
        
        # Create vectors for Pinecone (id, embedding, metadata)
        vectors = []
        for chunk, embedding in zip(chunks, embeddings):
            # Add text to metadata for retrieval
            metadata = chunk.metadata.copy()
            metadata['text'] = chunk.text
            
            vectors.append({
                'id': chunk.id,
                'values': embedding,
                'metadata': metadata
            })
        
        # Upsert in batches of 100 (Pinecone limit)
        batch_size = 100
        for i in range(0, len(vectors), batch_size):
            batch = vectors[i:i + batch_size]
            self.index.upsert(vectors=batch, namespace=self.namespace)
            print(f"Upserted batch {i//batch_size + 1}/{(len(vectors)-1)//batch_size + 1}")
        
        print(f"Successfully added {len(chunks)} chunks to Pinecone")
    
    def query(self, query: str, top_k: int = 5):
        """Query Pinecone index for similar chunks."""
        try:
            # Check if index is empty
            stats = self.index.describe_index_stats()
            total_vectors = stats.get('namespaces', {}).get(self.namespace, {}).get('vector_count', 0)
            
            if total_vectors == 0:
                print("Warning: Index is empty, returning no results")
                return {"ids": [[]], "documents": [[]], "metadatas": [[]], "distances": [[]]}
            
            # Generate query embedding
            query_embedding = self._generate_embeddings([query])[0]
            
            # Query Pinecone
            results = self.index.query(
                vector=query_embedding,
                top_k=top_k,
                namespace=self.namespace,
                include_metadata=True
            )
            
            # Format results to match ChromaDB structure
            ids = [[match['id'] for match in results['matches']]]
            documents = [[match['metadata'].get('text', '') for match in results['matches']]]
            metadatas = [[{k: v for k, v in match['metadata'].items() if k != 'text'} 
                          for match in results['matches']]]
            distances = [[1 - match['score'] for match in results['matches']]]  # Convert similarity to distance
            
            return {
                "ids": ids,
                "documents": documents,
                "metadatas": metadatas,
                "distances": distances
            }
        except Exception as e:
            print(f"Error querying Pinecone: {e}")
            import traceback
            traceback.print_exc()
            return {"ids": [[]], "documents": [[]], "metadatas": [[]], "distances": [[]]}
    
    def reset(self):
        """Reset the vector store by deleting all vectors in the namespace."""
        print(f"Resetting Pinecone namespace: {self.namespace}")
        
        try:
            # Delete all vectors in the namespace
            self.index.delete(delete_all=True, namespace=self.namespace)
            print(f"Successfully reset namespace {self.namespace}")
            
            # Wait a moment for deletion to propagate
            time.sleep(1)
            
            # Verify reset
            stats = self.index.describe_index_stats()
            count = stats.get('namespaces', {}).get(self.namespace, {}).get('vector_count', 0)
            print(f"Vector count after reset: {count}")
            
        except Exception as e:
            print(f"Error during reset: {e}")
            import traceback
            traceback.print_exc()
            raise
    
    def count(self):
        """Return the number of vectors in the namespace."""
        try:
            stats = self.index.describe_index_stats()
            count = stats.get('namespaces', {}).get(self.namespace, {}).get('vector_count', 0)
            return count
        except Exception as e:
            print(f"Error getting count: {e}")
            return 0
