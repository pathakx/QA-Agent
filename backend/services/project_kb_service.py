"""
Project-aware Knowledge Base service functions
Handles document ingestion and vector storage with project isolation
"""
import os
import uuid
import json
from backend.core.models import DocumentMeta
from backend.parsers.docs_parser import parse_document
from backend.parsers.text_chunker import chunk_text
from backend.parsers.html_parser import parse_html
from backend.core.vectorstore import VectorStore
from backend.core.supabase_client import create_user_client, create_client

def get_project_paths(project: dict):
    """Get directory paths for a project"""
    project_id = project['id']
    base_path = f"backend/data/projects/{project_id}"
    
    return {
        'doc_path': f"{base_path}/docs/",
        'html_path': f"{base_path}/html/",
        'ui_elements_path': f"{base_path}/ui_elements.json"
    }

def ingest_document_for_project(file_path: str, project: dict, vector_store: VectorStore) -> DocumentMeta:
    """Ingest a document into a project-specific vector store"""
    filename = os.path.basename(file_path)
    doc_id = str(uuid.uuid4())

    print(f"[Project: {project['name']}] Processing document: {filename}")
    
    # 1. Prevent Duplicates: Delete existing embeddings for this file
    vector_store.delete_document(filename)

    # 2. Parse text
    text = parse_document(file_path)
    
    # 3. Chunk text
    print(f"[Project: {project['name']}] Chunking document: {filename}")
    chunks = chunk_text(doc_id, text)
    
    # 4. Inject filename into metadata for future deletion
    for chunk in chunks:
        chunk.metadata["filename"] = filename

    print(f"[Project: {project['name']}] Created {len(chunks)} chunks from {filename}")
    
    before_count = vector_store.count()
    print(f"[Project: {project['name']}] Vector store count before adding: {before_count}")
    
    vector_store.add_chunks(chunks)
    
    after_count = vector_store.count()
    print(f"[Project: {project['name']}] Vector store count after adding: {after_count}")
    print(f"[Project: {project['name']}] Added {after_count - before_count} embeddings")

    return DocumentMeta(id=doc_id, filename=filename, doc_type=filename.split(".")[-1], path=file_path)

def ingest_html_for_project(file_path: str, project: dict):
    """Parse HTML file for a project"""
    paths = get_project_paths(project)
    elements = parse_html(file_path)
    
    with open(paths['ui_elements_path'], "w", encoding="utf-8") as f:
        json.dump([e.dict() for e in elements], f, indent=2)
    
    return elements

def get_project_kb_status(project: dict, vector_store: VectorStore):
    """Get knowledge base status for a specific project"""
    paths = get_project_paths(project)
    
    doc_files = os.listdir(paths['doc_path']) if os.path.exists(paths['doc_path']) else []
    html_files = os.listdir(paths['html_path']) if os.path.exists(paths['html_path']) else []
    
    embedding_count = vector_store.count()
    
    return {
        "project_id": project['id'],
        "project_name": project['name'],
        "doc_count": len(doc_files),
        "doc_files": doc_files,
        "html_parsed": os.path.exists(paths['ui_elements_path']),
        "html_files": [f for f in html_files if f.endswith(".html") or f.endswith(".htm")],
        "embedding_count": embedding_count
    }

def build_project_knowledge_base(project: dict, vector_store: VectorStore):
    """Build knowledge base for a specific project"""
    try:
        print(f"\n{'='*70}")
        print(f"BUILDING KNOWLEDGE BASE FOR PROJECT: {project['name']}")
        print(f"{'='*70}")
        
        paths = get_project_paths(project)
        doc_count = 0
        html_count = 0
        
        initial_count = vector_store.count()
        print(f"Initial embedding count: {initial_count}")
        
        # Ingest Docs
        if os.path.exists(paths['doc_path']):
            doc_files = os.listdir(paths['doc_path'])
            print(f"\nFound {len(doc_files)} documents to process")
            for f in doc_files:
                try:
                    print(f"\n--- Processing document: {f} ---")
                    doc_meta = ingest_document_for_project(
                        os.path.join(paths['doc_path'], f),
                        project,
                        vector_store
                    )
                    print(f"✓ Successfully ingested {f} (ID: {doc_meta.id})")
                    doc_count += 1
                except Exception as e:
                    print(f"✗ Error processing document {f}: {str(e)}")
                    import traceback
                    traceback.print_exc()
        else:
            print("\nNo documents directory found")
        
        # Ingest HTML
        if os.path.exists(paths['html_path']):
            html_files = [f for f in os.listdir(paths['html_path']) if f.endswith(".html") or f.endswith(".htm")]
            print(f"\nFound {len(html_files)} HTML files to process")
            for f in html_files:
                try:
                    print(f"\n--- Processing HTML: {f} ---")
                    elements = ingest_html_for_project(
                        os.path.join(paths['html_path'], f),
                        project
                    )
                    print(f"✓ Parsed {f}, found {len(elements)} UI elements")
                    html_count += 1
                except Exception as e:
                    print(f"✗ Error processing HTML {f}: {str(e)}")
                    import traceback
                    traceback.print_exc()
        else:
            print("\nNo HTML directory found")
        
        final_count = vector_store.count()
        embeddings_added = final_count - initial_count
        
        print(f"\n{'='*70}")
        print("BUILD SUMMARY")
        print(f"{'='*70}")
        print(f"Project: {project['name']}")
        print(f"Documents processed: {doc_count}")
        print(f"HTML files processed: {html_count}")
        print(f"Initial embeddings: {initial_count}")
        print(f"Final embeddings: {final_count}")
        print(f"Embeddings added: {embeddings_added}")
        print(f"{'='*70}\n")
        
        return {
            "status": "built",
            "project_id": project['id'],
            "project_name": project['name'],
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

def reset_project_knowledge_base(project: dict, vector_store: VectorStore, access_token: str = None):
    """Reset knowledge base for a specific project"""
    print(f"\n{'='*70}")
    print(f"RESETTING KNOWLEDGE BASE FOR PROJECT: {project['name']}")
    print(f"{'='*70}")
    
    try:
        paths = get_project_paths(project)
        import shutil
        
        # 1. Clear physical files
        print(f"Clearing physical files...")
        # Clear Docs
        if os.path.exists(paths['doc_path']):
            try:
                shutil.rmtree(paths['doc_path'])
                os.makedirs(paths['doc_path'])
                print(f"  - Cleared docs folder")
            except Exception as e:
                print(f"  - Failed to clear docs folder: {e}")
        
        # Clear HTML
        if os.path.exists(paths['html_path']):
            try:
                shutil.rmtree(paths['html_path'])
                os.makedirs(paths['html_path'])
                print(f"  - Cleared html folder")
            except Exception as e:
                print(f"  - Failed to clear html folder: {e}")
            
        # Clear UI elements JSON
        if os.path.exists(paths['ui_elements_path']):
            try:
                os.remove(paths['ui_elements_path'])
                print(f"  - Removed ui_elements.json")
            except Exception as e:
                 print(f"  - Failed to remove ui_elements.json: {e}")
    
        # Reset Vector DB
        print("\nResetting vector database...")
        vector_store.reset()
        
                # CLEAR DB TABLES
        try:
            print(f"[Project: {project['name']}] Clearing database tables...")
            
            # Note: We use the User Client (access_token) because the Environment Service Key  
            # appears to be the Anon Key (based on .env inspection), which cannot bypass RLS.
            # The User Client carries the Project Owner's permissions, which should be sufficient.
            
            if access_token:
                sb = create_user_client(access_token)
                print("✓ Using User Access Token for Reset")
            else:
                # Fallback to env key (likely anon) if no token, but this will likely fail RLS
                print("⚠️ No access token provided, attempting with env key (might fail RLS)")
                from backend.core.supabase_client import get_supabase_client
                sb = get_supabase_client()

            # Helper to delete and log with error handling
            def delete_and_log(table):
                try:
                    res = sb.table(table).delete().eq('project_id', project['id']).execute()
                    count = len(res.data) if res.data else 0
                    print(f"  - Deleted {count} records from {table}")
                except Exception as e:
                    # Log but continue - table might not exist or other issue
                    print(f"  ⚠️ Could not delete from {table}: {str(e)}")

            # Delete in order of dependency
            delete_and_log('validation_results')
            delete_and_log('autonomous_runs')
            delete_and_log('batch_runs')
            
            # Delete suite tests before suites
            try:
                suites_res = sb.table('test_suites').select('id').eq('project_id', project['id']).execute()
                if suites_res.data:
                    suite_ids = [s['id'] for s in suites_res.data]
                    st_res = sb.table('suite_tests').delete().in_('suite_id', suite_ids).execute()
                    print(f"  - Deleted {len(st_res.data) if st_res.data else 0} records from suite_tests")
            except Exception as e:
                 print(f"  ⚠️ Could not delete suite_tests: {str(e)}")
            
            delete_and_log('test_suites')
            delete_and_log('test_executions')
            delete_and_log('selenium_scripts')
            delete_and_log('testcases')
            delete_and_log('document_chunks')
            delete_and_log('kb_files')
            
            print(f"[Project: {project['name']}] Database tables cleared.")
        except Exception as db_e:
            print(f"[Project: {project['name']}] Error clearing DB: {db_e}")
            import traceback
            traceback.print_exc()
        
        final_count = vector_store.count()
        
        print(f"\n{'='*70}")
        print("RESET SUMMARY")
        print(f"{'='*70}")
        print(f"Project: {project['name']}")
        print(f"Final embedding count: {final_count}")
        print("✓ Knowledge base reset complete")
        print(f"{'='*70}\n")
        
        return {
            "status": "reset",
            "project_id": project['id'],
            "project_name": project['name'],
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
