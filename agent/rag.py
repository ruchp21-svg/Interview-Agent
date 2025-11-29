"""
Simple RAG helper that wraps a local Chroma DB and provides add/query helpers.
This is intentionally lightweight; replace or extend with LangChain connectors in production.
"""
from typing import List, Dict, Optional

try:
    import chromadb
    from chromadb.config import Settings
    CHROMA_AVAILABLE = True
except Exception:
    CHROMA_AVAILABLE = False


class SimpleVectorStore:
    def __init__(self, persist_directory: Optional[str] = None):
        if not CHROMA_AVAILABLE:
            raise RuntimeError("chromadb is not installed")
        self.client = chromadb.Client(Settings(chroma_db_impl="duckdb+parquet", persist_directory=persist_directory))
        self.collection = None

    def create_collection(self, name: str):
        self.collection = self.client.create_collection(name=name)
        return self.collection

    def add_documents(self, texts: List[str], metadatas: Optional[List[Dict]] = None, ids: Optional[List[str]] = None):
        if not self.collection:
            raise RuntimeError("Collection not created")
        # Chromadb expects list of documents and metadatas and ids
        self.collection.add(documents=texts, metadatas=metadatas or [{} for _ in range(len(texts))], ids=ids)

    def query(self, query_text: str, n_results: int = 3):
        if not self.collection:
            raise RuntimeError("Collection not created")
        res = self.collection.query(query_texts=[query_text], n_results=n_results)
        return res


# Placeholder pinecone adapter (requires pinecone client and an API key)
class PineconeAdapter:
    def __init__(self, index_name: str, api_key: str = None, environment: str = None):
        try:
            import pinecone
        except Exception as e:
            raise RuntimeError("pinecone-client is required for PineconeAdapter")
        self.api_key = api_key
        self.environment = environment
        pinecone.init(api_key=self.api_key, environment=self.environment)
        self.index = pinecone.Index(index_name)

    def upsert(self, vectors):
        self.index.upsert(vectors=vectors)

    def query(self, vector, top_k=5):
        return self.index.query(vector=vector, top_k=top_k)
