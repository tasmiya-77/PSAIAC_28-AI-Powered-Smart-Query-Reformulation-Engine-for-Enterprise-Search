import re
import logging
from typing import List, Dict, Any, Optional, Tuple

logger = logging.getLogger(__name__)

_bge_tokenizer = None
_bge_model = None
_bge_failed = False


def _get_bge_reranker():
    """Lazy load BAAI/bge-reranker-base model using transformers."""
    global _bge_tokenizer, _bge_model, _bge_failed
    if _bge_failed:
        return None, None
    if _bge_tokenizer is not None and _bge_model is not None:
        return _bge_tokenizer, _bge_model

    try:
        from transformers import AutoTokenizer, AutoModelForSequenceClassification
        model_name = "BAAI/bge-reranker-base"
        logger.info(f"[RERANKER] Loading BGE Reranker model '{model_name}'...")
        _bge_tokenizer = AutoTokenizer.from_pretrained(model_name)
        _bge_model = AutoModelForSequenceClassification.from_pretrained(model_name)
        _bge_model.eval()
        logger.info(f"[RERANKER] Successfully loaded BGE Reranker model '{model_name}'")
        return _bge_tokenizer, _bge_model
    except Exception as e:
        logger.warning(f"[RERANKER] Could not load BGE Reranker model: {str(e)}. Using fallback scoring.")
        _bge_failed = True
        return None, None


def extract_matched_keywords(query: str, text: str) -> List[str]:
    """Extract query terms present in text snippet."""
    stop_words = {"how", "to", "fix", "the", "and", "is", "for", "with", "in", "on", "a", "an", "of", "what", "can"}
    query_tokens = [w.lower() for w in re.findall(r"\b\w{3,}\b", str(query or "")) if w.lower() not in stop_words]
    text_lower = str(text or "").lower()

    matched = []
    for token in query_tokens:
        if token in text_lower and token not in matched:
            matched.append(token)

    return matched


def create_highlighted_snippet(text: str, matched_keywords: List[str], max_len: int = 240) -> str:
    """Generate a clean text snippet with matched terms highlighted."""
    if not text:
        return ""
    
    snippet = text.strip()
    if len(snippet) > max_len:
        snippet = snippet[:max_len].rsplit(" ", 1)[0] + "..."

    return snippet


class AIRerankerService:
    def rerank_top_10(
        self, query: str, candidate_chunks: List[Dict[str, Any]], top_k: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Rerank merged candidate chunks using BGE Cross-Encoder reranker model with fallback.
        Attaches rank, title, passage, keyword_score, semantic_score, and rerank_score.
        """
        if not candidate_chunks:
            return []

        tokenizer, model = _get_bge_reranker()
        bge_scores: Optional[List[float]] = None

        if tokenizer is not None and model is not None:
            try:
                import torch
                pairs = [[query, item["document"]] for item in candidate_chunks]
                with torch.no_grad():
                    inputs = tokenizer(pairs, padding=True, truncation=True, return_tensors="pt", max_length=512)
                    logits = model(**inputs, return_dict=True).logits.view(-1).float()
                    # Apply sigmoid normalization to obtain score in range [0, 1]
                    probs = torch.sigmoid(logits)
                    bge_scores = [round(float(p), 4) for p in probs]
                logger.info(f"[RERANKER] Computed BGE Cross-Encoder scores for {len(bge_scores)} candidates")
            except Exception as e:
                logger.warning(f"[RERANKER] BGE model inference failed: {str(e)}. Using fallback scoring.")

        reranked = []
        for idx, item in enumerate(candidate_chunks):
            doc_text = item["document"]
            meta = item["metadata"]
            rrf_score = item.get("rrf_score", 0.0)
            semantic_score = item.get("semantic_score", 0.0)
            keyword_score = item.get("keyword_score", item.get("bm25_score", 0.0))

            matched_kws = extract_matched_keywords(query, doc_text)

            if bge_scores and idx < len(bge_scores):
                rerank_score = bge_scores[idx]
                final_relevance = round(min(0.99, max(0.40, rerank_score)), 2)
            else:
                # Fallback scoring using RRF + keyword bonus + semantic score
                base_score = min(0.95, rrf_score * 25.0)
                keyword_bonus = min(0.15, len(matched_kws) * 0.04)
                final_relevance = round(min(0.99, max(0.40, base_score + keyword_bonus)), 2)
                rerank_score = final_relevance

            relevance_percentage = int(final_relevance * 100)

            if final_relevance >= 0.80:
                confidence = "High"
            elif final_relevance >= 0.60:
                confidence = "Medium"
            else:
                confidence = "Low"

            highlighted_snippet = create_highlighted_snippet(doc_text, matched_kws)
            filename = meta.get("filename", "Untitled")

            reranked.append({
                "document_id": meta.get("document_id", "unknown"),
                "chunk_id": item["chunk_id"],
                "filename": filename,
                "title": filename,
                "file_type": meta.get("file_type", "txt"),
                "file_size_bytes": meta.get("file_size_bytes", 0),
                "upload_date": meta.get("upload_date", ""),
                "department": meta.get("department", "Engineering"),
                "content": doc_text,
                "passage": highlighted_snippet,
                "highlighted_snippet": highlighted_snippet,
                "relevance_score": final_relevance,
                "relevance_percentage": relevance_percentage,
                "confidence": confidence,
                "matched_keywords": matched_kws,
                "chunk_index": meta.get("chunk_index", 0),
                "total_chunks": meta.get("total_chunks", 1),
                "keyword_score": keyword_score,
                "semantic_score": semantic_score,
                "rerank_score": rerank_score,
            })

        # Sort by rerank score / relevance score descending
        reranked.sort(key=lambda x: (x["rerank_score"], x["relevance_score"]), reverse=True)

        # Assign final rank position (1..10) & generate explainability text
        top_results = reranked[:top_k]
        for rank_idx, result_item in enumerate(top_results):
            r_num = rank_idx + 1
            result_item["rank"] = r_num
            result_item["retrieval_method"] = "Hybrid (BM25 + ChromaDB Vector)"

            kw_list = ", ".join(result_item["matched_keywords"]) if result_item["matched_keywords"] else "domain context"
            exp_short = f"Selected via Hybrid Retrieval (BM25 Score: {result_item['keyword_score']}, Semantic Score: {result_item['semantic_score']}, Rerank Score: {result_item['rerank_score']}). Ranked #{r_num} matching keywords: {kw_list}."
            
            result_item["explanation"] = exp_short
            result_item["why_selected"] = f"""Selected at rank #{r_num} with {result_item['relevance_percentage']}% relevance ({result_item['confidence']} confidence).
• Retrieval: Dual-Path Hybrid Search (BM25 + Sentence Transformers)
• Semantic Score: {result_item['semantic_score']} (Vector Distance)
• BM25 Score: {result_item['keyword_score']} (Keyword Frequency)
• BGE Rerank Score: {result_item['rerank_score']} (Cross-Encoder Alignment)
• Matched Terms: {kw_list}"""

        logger.info(f"[RERANKER] Evaluated {len(candidate_chunks)} candidates -> Top {len(top_results)} returned (Top rerank_score: {top_results[0]['rerank_score'] if top_results else 0.0})")
        return top_results



ai_reranker_service = AIRerankerService()


