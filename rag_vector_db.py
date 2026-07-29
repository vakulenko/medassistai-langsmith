"""Vector database RAG system for doctor profiles and patient data."""
import os
from typing import List, Optional, Dict
from config import GOOGLE_API_KEY

# Try importing from newer langchain package structure
try:
    from langchain_text_splitters import RecursiveCharacterTextSplitter
except ImportError:
    try:
        from langchain.text_splitter import RecursiveCharacterTextSplitter
    except ImportError:
        raise ImportError("langchain_text_splitters or langchain.text_splitter not found. Run: pip install -r requirements.txt")

try:
    from langchain_chroma import Chroma
except ImportError:
    raise ImportError("langchain_chroma not found. Run: pip install langchain-chroma")

try:
    from langchain_google_genai import GoogleGenerativeAIEmbeddings
except ImportError:
    raise ImportError("langchain_google_genai not found. Run: pip install langchain-google-genai")

try:
    from langchain_core.documents import Document
except ImportError:
    try:
        from langchain.schema import Document
    except ImportError:
        raise ImportError("langchain_core not found. Run: pip install langchain-core")


class RAGVectorDB:
    """RAG system using Chroma vector database."""

    def __init__(self, persist_dir: str = ".vector_db"):
        """Initialize RAG vector database."""
        self.persist_dir = persist_dir

        # Try embedding models in order of preference
        # Based on: python CHECK_GEMINI_MODELS.py
        embedding_models = [
            "models/gemini-embedding-2",           # Best quality
            "models/gemini-embedding-2-preview",   # Preview version
            "models/gemini-embedding-001",         # Legacy
        ]

        embeddings = None
        for model in embedding_models:
            try:
                embeddings = GoogleGenerativeAIEmbeddings(model=model, google_api_key=GOOGLE_API_KEY)
                # Test the model
                test_embedding = embeddings.embed_query("test")
                print(f"[OK] Using embedding model: {model}")
                break
            except Exception as e:
                continue

        if not embeddings:
            raise ValueError(
                "No embedding models available. Run: python CHECK_GEMINI_MODELS.py"
            )

        self.embeddings = embeddings
        self.vector_store = None
        self.load_or_create_db()

    def load_or_create_db(self):
        """Load existing vector DB or create new one."""
        if os.path.exists(self.persist_dir):
            self.vector_store = Chroma(
                persist_directory=self.persist_dir,
                embedding_function=self.embeddings,
                collection_name="medassistai"
            )
            print(f"[OK] Loaded existing vector database from {self.persist_dir}")
        else:
            self.vector_store = Chroma(
                persist_directory=self.persist_dir,
                embedding_function=self.embeddings,
                collection_name="medassistai"
            )
            print(f"[OK] Created new vector database at {self.persist_dir}")

    def add_documents(self, documents: Dict[str, str], chunk_size: int = 1000, chunk_overlap: int = 200):
        """Add documents to vector store."""
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=["\n\n", "\n", " ", ""]
        )

        all_docs = []

        for doc_type, content in documents.items():
            if not content:
                continue

            chunks = text_splitter.split_text(content)
            for i, chunk in enumerate(chunks):
                doc = Document(
                    page_content=chunk,
                    metadata={
                        "type": doc_type,
                        "chunk": i
                    }
                )
                all_docs.append(doc)

        if all_docs:
            self.vector_store.add_documents(all_docs)
            # Note: Newer Chroma versions auto-persist, no need to call persist()
            print(f"[OK] Added {len(all_docs)} chunks to vector database")
        else:
            print("[WARN] No documents to add")

    def retrieve_relevant_context(self, query: str, top_k: int = 5) -> List[str]:
        """Retrieve relevant context for a query."""
        if not self.vector_store:
            return []

        try:
            results = self.vector_store.similarity_search(query, k=top_k)
            return [doc.page_content for doc in results]
        except Exception as e:
            print(f"Error retrieving context: {e}")
            return []

    def retrieve_by_type(self, query: str, doc_type: str, top_k: int = 5) -> List[str]:
        """Retrieve relevant context filtered by document type."""
        if not self.vector_store:
            return []

        try:
            results = self.vector_store.similarity_search(
                query,
                k=top_k * 2,
                filter={"type": doc_type}
            )
            return [doc.page_content for doc in results[:top_k]]
        except Exception as e:
            print(f"Error retrieving context by type: {e}")
            return []

    def get_doctor_info(self, doctor_name: str) -> Optional[str]:
        """Get specific doctor information."""
        context = self.retrieve_by_type(doctor_name, "doctor_profiles", top_k=3)
        if context:
            return "\n".join(context)
        return None

    def get_patient_info(self, patient_name: str) -> Optional[str]:
        """Get patient information."""
        context = self.retrieve_by_type(f"patient {patient_name}", "patient_data", top_k=3)
        if context:
            return "\n".join(context)
        return None

    def clear_db(self):
        """Clear all documents from vector store."""
        if self.vector_store:
            # Chromadb doesn't have a direct clear method, so we delete and recreate
            import shutil
            if os.path.exists(self.persist_dir):
                shutil.rmtree(self.persist_dir)
            self.load_or_create_db()
            print(f"[OK] Cleared vector database")

    def get_db_stats(self) -> Dict:
        """Get statistics about vector database."""
        if not self.vector_store:
            return {}

        try:
            collection = self.vector_store._collection
            count = collection.count()
            return {
                "total_chunks": count,
                "persist_dir": self.persist_dir
            }
        except Exception as e:
            print(f"Error getting DB stats: {e}")
            return {}


def initialize_rag_db(persist_dir: str = ".vector_db") -> RAGVectorDB:
    """Initialize RAG vector database."""
    return RAGVectorDB(persist_dir=persist_dir)
