import re
import math
import logging
from typing import List, Dict, Any, Tuple
from app.services.vector_store import vector_store_service

logger = logging.getLogger(__name__)


def compute_bm25_scores(
    query: str, documents: List[str], k1: float = 1.5, b: float = 0.75
) -> List[float]:
    """
    Compute BM25 lexical relevance scores for query over documents.
    """
    query_tokens = [w.lower() for w in re.findall(r"\b\w+\b", str(query or ""))]
    if not query_tokens or not documents:
        return [0.0] * len(documents)

    doc_tokens_list = [
        [w.lower() for w in re.findall(r"\b\w+\b", str(doc or ""))] for doc in documents
    ]
    total_docs = len(documents)
    avg_dl = sum(len(d) for d in doc_tokens_list) / max(1, total_docs)

    # Document frequency (DF) for query tokens
    df = {}
    for token in query_tokens:
        df[token] = sum(1 for d in doc_tokens_list if token in d)

    scores = []
    for d_tokens in doc_tokens_list:
        doc_len = len(d_tokens)
        score = 0.0
        term_freqs = {}
        for t in d_tokens:
            term_freqs[t] = term_freqs.get(t, 0) + 1

        for q_token in query_tokens:
            if q_token in term_freqs:
                tf = term_freqs[q_token]
                n_q = df.get(q_token, 0)
                # Inverse Document Frequency (IDF)
                idf = math.log((total_docs - n_q + 0.5) / (n_q + 0.5) + 1.0)
                # BM25 Term Weight
                numerator = tf * (k1 + 1)
                denominator = tf + k1 * (1 - b + b * (doc_len / max(1.0, avg_dl)))
                score += idf * (numerator / denominator)

        scores.append(round(score, 4))

    return scores


class HybridRetrievalService:
    def __init__(self):
        self.vector_store = vector_store_service

    def retrieve_top_50(
        self,
        query: str,
        filters: Dict[str, Any] = None,
        top_k: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Execute Hybrid Retrieval (Vector + BM25 Lexical) with RRF score fusion.
        Retrieves Top 50 candidates.
        """
        try:
            collection = self.vector_store._get_collection()
            
            # Build ChromaDB filter query
            chroma_where = None
            if filters:
                where_clauses = []
                if filters.get("file_type") and filters["file_type"] != "all":
                    where_clauses.append({"file_type": filters["file_type"].lower()})

                if len(where_clauses) == 1:
                    chroma_where = where_clauses[0]
                elif len(where_clauses) > 1:
                    chroma_where = {"$and": where_clauses}

            # 1. Vector Search via ChromaDB
            query_kwargs = {
                "query_texts": [query],
                "n_results": min(top_k * 2, max(50, collection.count())),
                "include": ["documents", "metadatas", "distances"]
            }
            if chroma_where:
                query_kwargs["where"] = chroma_where

            vector_results = collection.query(**query_kwargs)

            vector_docs = vector_results.get("documents", [[]])[0] or []
            vector_metas = vector_results.get("metadatas", [[]])[0] or []
            vector_ids = vector_results.get("ids", [[]])[0] or []
            vector_dists = vector_results.get("distances", [[]])[0] or []

            if not vector_docs:
                return []


            # 2. Compute BM25 Lexical Scores over candidate set
            bm25_scores = compute_bm25_scores(query, vector_docs)

            # 3. Reciprocal Rank Fusion (RRF)
            # Rank by vector distance (smaller distance = higher rank)
            vector_ranked_indices = sorted(range(len(vector_dists)), key=lambda i: vector_dists[i])
            # Rank by BM25 score (larger score = higher rank)
            bm25_ranked_indices = sorted(range(len(bm25_scores)), key=lambda i: bm25_scores[i], reverse=True)

            vector_rank_map = {idx: rank + 1 for rank, idx in enumerate(vector_ranked_indices)}
            bm25_rank_map = {idx: rank + 1 for rank, idx in enumerate(bm25_ranked_indices)}

            rrf_candidates = []
            seen_chunk_ids = set()

            k_rrf = 60  # RRF constant factor
            for idx in range(len(vector_docs)):
                chunk_id = vector_ids[idx]
                if chunk_id in seen_chunk_ids:
                    continue
                seen_chunk_ids.add(chunk_id)

                v_rank = vector_rank_map.get(idx, 100)
                b_rank = bm25_rank_map.get(idx, 100)

                dist = vector_dists[idx] if idx < len(vector_dists) else 1.0
                # Compute normalized semantic similarity score (0.0 to 1.0)
                semantic_score = round(max(0.0, min(1.0, 1.0 - (dist / 2.0) if dist <= 2.0 else 1.0 / (1.0 + dist))), 4)
                keyword_score = round(float(bm25_scores[idx]), 4) if idx < len(bm25_scores) else 0.0

                # RRF Score calculation
                rrf_score = (1.0 / (k_rrf + v_rank)) + (1.0 / (k_rrf + b_rank))

                rrf_candidates.append({
                    "chunk_id": chunk_id,
                    "document": vector_docs[idx],
                    "metadata": vector_metas[idx],
                    "vector_distance": dist,
                    "semantic_score": semantic_score,
                    "keyword_score": keyword_score,
                    "bm25_score": keyword_score,
                    "rrf_score": rrf_score,
                })

            # Sort by RRF score descending
            rrf_candidates.sort(key=lambda x: x["rrf_score"], reverse=True)

            logger.info(f"[RETRIEVAL] Hybrid search fetched {len(rrf_candidates[:top_k])} candidates for reformulated query '{query}'")
            return rrf_candidates[:top_k]


        except Exception as e:
            logger.error(f"[RETRIEVAL] Error in hybrid retrieval: {str(e)}")
            return []


hybrid_retrieval_service = HybridRetrievalService()

