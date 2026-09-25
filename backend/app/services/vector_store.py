import uuid
import logging
import math
import re
from typing import List, Dict, Any, Optional, Tuple, Union
from app.core.config import settings
from app.core.db import get_chroma_client

logger = logging.getLogger(__name__)


class FastFeatureEmbeddingFunction:
    """
    Fallback 384-dimensional feature embedding function (deterministic n-gram/TF vectorizer).
    """
    name: str = "fast_feature_embeddings"

    def __init__(self, vector_dim: int = 384):
        self.vector_dim = vector_dim

    def name(self) -> str:
        return "fast_feature_embeddings"

    def _embed_single_text(self, text: str) -> List[float]:
        vec = [0.0] * self.vector_dim
        if not text or not isinstance(text, str):
            return vec

        clean_text = text.lower()
        words = re.findall(r"\b\w+\b", clean_text)
        
        for word in words:
            idx = abs(hash(word)) % self.vector_dim
            vec[idx] += 1.0

        for i in range(len(clean_text) - 2):
            ngram = clean_text[i:i+3]
            idx = abs(hash(ngram)) % self.vector_dim
            vec[idx] += 0.5

        norm = math.sqrt(sum(x * x for x in vec))
        if norm > 0:
            vec = [round(x / norm, 6) for x in vec]

        return vec

    def embed_query(self, input: Any) -> List[List[float]]:
        if isinstance(input, str):
            input = [input]
        return [self._embed_single_text(t) for t in input]

    def embed_documents(self, input: List[str]) -> List[List[float]]:
        return [self._embed_single_text(t) for t in input]

    def __call__(self, input: Union[str, List[str]]) -> List[List[float]]:
        if isinstance(input, str):
            input = [input]
        return [self._embed_single_text(t) for t in input]


_cached_embedding_fn = None


def get_embedding_function():
    """
    Return SentenceTransformers embedding function (Primary) or FastFeature embedding function (Fallback).
    Satisfies ChromaDB EmbeddingFunction protocol.
    """
    global _cached_embedding_fn
    if _cached_embedding_fn is not None:
        return _cached_embedding_fn

    try:
        from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction
        model_name = settings.EMBEDDING_MODEL_NAME or "all-MiniLM-L6-v2"
        logger.info(f"[VECTOR_STORE] Initializing SentenceTransformers embedding function with model '{model_name}'")
        _cached_embedding_fn = SentenceTransformerEmbeddingFunction(model_name=model_name)
        return _cached_embedding_fn
    except Exception as e:
        logger.warning(f"[VECTOR_STORE] SentenceTransformers embedding initialization warning: {str(e)}. Using FastFeature fallback.")
        _cached_embedding_fn = FastFeatureEmbeddingFunction()
        return _cached_embedding_fn


class VectorStoreService:
    def __init__(self):
        self.client = get_chroma_client()
        self.collection_name = settings.CHROMADB_COLLECTION_NAME
        self._collection = None

    def _get_collection(self):
        if self._collection is not None:
            return self._collection
        if self.client is None:
            raise RuntimeError("ChromaDB client is unavailable.")

        emb_fn = get_embedding_function()
        try:
            self._collection = self.client.get_collection(
                name=self.collection_name,
                embedding_function=emb_fn
            )
        except Exception as e:
            logger.info(f"[VECTOR_STORE] Creating collection '{self.collection_name}': {str(e)}")
            try:
                self.client.delete_collection(name=self.collection_name)
            except Exception:
                pass

            self._collection = self.client.create_collection(
                name=self.collection_name,
                embedding_function=emb_fn,
                metadata={"description": "Vector store for Smart Query Reformulation Engine"}
            )
        return self._collection

    def is_duplicate_hash(self, file_hash: str) -> Optional[Dict[str, Any]]:
        """Check if a file with matching SHA-256 hash already exists in vector store."""
        try:
            collection = self._get_collection()
            results = collection.get(
                where={"file_hash": file_hash},
                limit=1
            )
            if results and results.get("ids") and len(results["ids"]) > 0:
                metadatas = results.get("metadatas", [])
                if metadatas and len(metadatas) > 0:
                    logger.info(f"[VECTOR_STORE] Found duplicate file hash '{file_hash[:10]}...' in collection.")
                    return metadatas[0]
            return None
        except Exception as e:
            logger.warning(f"[VECTOR_STORE] Error checking duplicate hash: {str(e)}")
            return None

    def add_document_chunks(
        self,
        document_id: str,
        chunks: List[str],
        metadata: Dict[str, Any]
    ) -> int:
        """Store document chunks and metadata in ChromaDB."""
        collection = self._get_collection()

        ids = [f"{document_id}_chunk_{idx}" for idx in range(len(chunks))]
        chunk_metadatas = []
        for idx in range(len(chunks)):
            chunk_meta = {
                "document_id": document_id,
                "filename": metadata["filename"],
                "file_type": metadata["file_type"],
                "file_size_bytes": metadata["file_size_bytes"],
                "file_hash": metadata["file_hash"],
                "upload_date": metadata["upload_date"],
                "chunk_index": idx,
                "total_chunks": len(chunks)
            }
            chunk_metadatas.append(chunk_meta)

        collection.add(
            ids=ids,
            documents=chunks,
            metadatas=chunk_metadatas
        )

        logger.info(f"[VECTOR_STORE] Indexed {len(chunks)} vector chunks for document '{metadata['filename']}' ({document_id}) into ChromaDB")
        return len(chunks)

    def list_documents(self) -> Tuple[List[Dict[str, Any]], int]:
        """List distinct ingested documents with chunk counts."""
        collection = self._get_collection()
        all_records = collection.get(include=["metadatas"])
        metadatas = all_records.get("metadatas", []) or []

        docs_map: Dict[str, Dict[str, Any]] = {}
        total_chunks = len(metadatas)

        for meta in metadatas:
            doc_id = meta.get("document_id")
            if not doc_id:
                continue
            if doc_id not in docs_map:
                docs_map[doc_id] = {
                    "document_id": doc_id,
                    "filename": meta.get("filename", "Unknown"),
                    "file_type": meta.get("file_type", "unknown"),
                    "file_size_bytes": meta.get("file_size_bytes", 0),
                    "chunk_count": meta.get("total_chunks", 1),
                    "upload_date": meta.get("upload_date", ""),
                }

        logger.info(f"[VECTOR_STORE] Listed {len(docs_map)} distinct documents ({total_chunks} total vector chunks)")
        return list(docs_map.values()), total_chunks

    def delete_document(self, document_id: str) -> int:
        """Delete all vector embeddings & chunks for a specific document_id."""
        collection = self._get_collection()
        results = collection.get(where={"document_id": document_id})
        ids = results.get("ids", []) or []
        deleted_count = len(ids)

        if deleted_count > 0:
            collection.delete(where={"document_id": document_id})
            logger.info(f"[VECTOR_STORE] Deleted {deleted_count} vector chunks for document_id {document_id}")

        return deleted_count


vector_store_service = VectorStoreService()

