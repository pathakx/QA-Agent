import os
import uuid
import json
from backend.core.models import DocumentMeta
from backend.parsers.docs_parser import parse_document
from backend.parsers.text_chunker import chunk_text
from backend.parsers.html_parser import parse_html
from backend.core.vectorstore import PineconeVectorStore

# Global vector store instance
_vector_store = None

DOC_PATH = "backend/data/docs/"
HTML_PATH = "backend/data/html/ui_elements.json"

def get_vector_store():
    """Get or create the Pinecone vector store instance."""
    global _vector_store
    if _vector_store is None:
        print("Initializing Pinecone vector store instance")
        _vector_store = PineconeVectorStore()
    return _vector_store

def reinitialize_vector_store():
    """Force reinitialize the Pinecone vector store instance."""
    global _vector_store
    print("Reinitializing Pinecone vector store instance")
    _vector_store = PineconeVectorStore()
    return _vector_store

def ingest_document(file_path: str) -> DocumentMeta:
    filename = os.path.basename(file_path)
    doc_id = str(uuid.uuid4())

    print(f"Parsing document: {filename}")
    text = parse_document(file_path)
    
    print(f"Chunking document: {filename}")
    chunks = chunk_text(doc_id, text)
    print(f"Created {len(chunks)} chunks from {filename}")
    
    # Get fresh vector store reference
    vs = get_vector_store()
    before_count = vs.count()
    print(f"Vector store count before adding: {before_count}")
    
    vs.add_chunks(chunks)
    
    after_count = vs.count()
    print(f"Vector store count after adding: {after_count}")
    print(f"Added {after_count - before_count} embeddings")

    return DocumentMeta(id=doc_id, filename=filename, doc_type=filename.split(".")[-1], path=file_path)

def ingest_html(file_path: str):
    elements = parse_html(file_path)
    with open(HTML_PATH, "w", encoding="utf-8") as f:
        json.dump([e.dict() for e in elements], f, indent=2)
    return elements

def get_kb_status():
    doc_files = os.listdir(DOC_PATH) if os.path.exists(DOC_PATH) else []
    html_files = os.listdir("backend/data/html/") if os.path.exists("backend/data/html/") else []
    
    # Get actual embedding count from vector store
    vs = get_vector_store()
    embedding_count = vs.count()
    
    return {
        "doc_count": len(doc_files),
        "doc_files": doc_files,
        "html_parsed": os.path.exists(HTML_PATH),
        "html_files": [f for f in html_files if f.endswith(".html") or f.endswith(".htm")],
        "embedding_count": embedding_count
    }

def build_knowledge_base():
    try:
        print("\n" + "="*70)
        print("BUILDING KNOWLEDGE BASE")
        print("="*70)
        
        doc_count = 0
        html_count = 0
        
        # Get vector store and check initial state
        vs = get_vector_store()
        initial_count = vs.count()
        print(f"Initial embedding count: {initial_count}")
        
        # Ingest Docs
        if os.path.exists(DOC_PATH):
            doc_files = os.listdir(DOC_PATH)
            print(f"\nFound {len(doc_files)} documents to process")
            for f in doc_files:
                try:
                    print(f"\n--- Processing document: {f} ---")
                    doc_meta = ingest_document(os.path.join(DOC_PATH, f))
                    print(f"✓ Successfully ingested {f} (ID: {doc_meta.id})")
                    doc_count += 1
                except Exception as e:
                    print(f"✗ Error processing document {f}: {str(e)}")
                    import traceback
                    traceback.print_exc()
        else:
            print("\nNo documents directory found")
        
        # Ingest HTML
        html_dir = "backend/data/html/"
        if os.path.exists(html_dir):
            html_files = [f for f in os.listdir(html_dir) if f.endswith(".html") or f.endswith(".htm")]
            print(f"\nFound {len(html_files)} HTML files to process")
            for f in html_files:
                try:
                    print(f"\n--- Processing HTML: {f} ---")
                    elements = ingest_html(os.path.join(html_dir, f))
                    print(f"✓ Parsed {f}, found {len(elements)} UI elements")
                    html_count += 1
                except Exception as e:
                    print(f"✗ Error processing HTML {f}: {str(e)}")
                    import traceback
                    traceback.print_exc()
        else:
            print("\nNo HTML directory found")
        
        # Verify embeddings were created
        final_count = vs.count()
        embeddings_added = final_count - initial_count
        
        print("\n" + "="*70)
        print("BUILD SUMMARY")
        print("="*70)
        print(f"Documents processed: {doc_count}")
        print(f"HTML files processed: {html_count}")
        print(f"Initial embeddings: {initial_count}")
        print(f"Final embeddings: {final_count}")
        print(f"Embeddings added: {embeddings_added}")
        print("="*70 + "\n")
        
        # Check if build was successful
        if doc_count > 0 and embeddings_added == 0:
            print("⚠️ WARNING: Documents were processed but no embeddings were added!")
            return {
                "status": "warning",
                "documents_processed": doc_count,
                "html_processed": html_count,
                "embedding_count": final_count,
                "warning": "Documents processed but no embeddings created"
            }
        
        return {
            "status": "built",
            "documents_processed": doc_count,
            "html_processed": html_count,
            "embedding_count": final_count,
            "embeddings_added": embeddings_added
        }
    except Exception as e:
        print(f"\n❌ ERROR building knowledge base: {str(e)}")
        import traceback
        traceback.print_exc()
        return {
            "status": "error",
            "error": str(e)
        }

def reset_knowledge_base():
    print("\n" + "="*70)
    print("RESETTING KNOWLEDGE BASE")
    print("="*70)
    
    try:
        # Clear Docs
        if os.path.exists(DOC_PATH):
            doc_files = os.listdir(DOC_PATH)
            print(f"Removing {len(doc_files)} document files...")
            for f in doc_files:
                os.remove(os.path.join(DOC_PATH, f))
            print("✓ Document files removed")
                
        # Clear HTML
        html_dir = "backend/data/html/"
        if os.path.exists(html_dir):
            html_files = os.listdir(html_dir)
            print(f"Removing {len(html_files)} HTML files...")
            for f in html_files:
                os.remove(os.path.join(html_dir, f))
            print("✓ HTML files removed")
    
        # Reset Vector DB
        print("\nResetting vector database...")
        vs = get_vector_store()
        vs.reset()
        
        # Reinitialize the vector store instance to get a fresh reference
        print("Reinitializing vector store instance...")
        reinitialize_vector_store()
        
        # Verify reset
        vs_new = get_vector_store()
        final_count = vs_new.count()
        
        print("\n" + "="*70)
        print("RESET SUMMARY")
        print("="*70)
        print(f"Final embedding count: {final_count}")
        print("✓ Knowledge base reset complete")
        print("="*70 + "\n")
        
        return {
            "status": "reset",
            "embedding_count": final_count
        }
    except Exception as e:
        print(f"\n❌ ERROR during reset: {e}")
        import traceback
        traceback.print_exc()
        return {
            "status": "error",
            "error": str(e)
        }
