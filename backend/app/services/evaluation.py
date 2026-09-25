import math
import time
import logging
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class BenchmarkQuery(BaseModel):
    query: str
    target_filenames: List[str]
    description: Optional[str] = None


class EvaluationMetricsResult(BaseModel):
    total_queries: int
    precision_at_1: float
    precision_at_3: float
    precision_at_5: float
    precision_at_10: float
    recall_at_1: float
    recall_at_3: float
    recall_at_5: float
    recall_at_10: float
    mrr: float
    ndcg_at_5: float
    ndcg_at_10: float
    avg_latency_ms: float
    query_details: List[Dict[str, Any]]


def calculate_precision_at_k(retrieved_docs: List[str], target_docs: List[str], k: int) -> float:
    """Calculate Precision@K."""
    if k <= 0 or not retrieved_docs or not target_docs:
        return 0.0
    cutoff = retrieved_docs[:k]
    hits = sum(1 for doc in cutoff if any(target.lower() in doc.lower() for target in target_docs))
    return round(hits / float(k), 4)


def calculate_recall_at_k(retrieved_docs: List[str], target_docs: List[str], k: int) -> float:
    """Calculate Recall@K."""
    if k <= 0 or not retrieved_docs or not target_docs:
        return 0.0
    cutoff = retrieved_docs[:k]
    matched_targets = set()
    for doc in cutoff:
        for target in target_docs:
            if target.lower() in doc.lower():
                matched_targets.add(target.lower())
    return round(len(matched_targets) / float(len(target_docs)), 4)


def calculate_reciprocal_rank(retrieved_docs: List[str], target_docs: List[str]) -> float:
    """Calculate Reciprocal Rank (1 / rank of first relevant doc)."""
    if not retrieved_docs or not target_docs:
        return 0.0
    for idx, doc in enumerate(retrieved_docs):
        if any(target.lower() in doc.lower() for target in target_docs):
            return round(1.0 / float(idx + 1), 4)
    return 0.0


def calculate_ndcg_at_k(retrieved_docs: List[str], target_docs: List[str], k: int) -> float:
    """Calculate Normalized Discounted Cumulative Gain at K (NDCG@K)."""
    if k <= 0 or not retrieved_docs or not target_docs:
        return 0.0

    cutoff = retrieved_docs[:k]
    dcg = 0.0
    rel_scores = []
    for idx, doc in enumerate(cutoff):
        rel = 1.0 if any(target.lower() in doc.lower() for target in target_docs) else 0.0
        rel_scores.append(rel)
        if rel > 0:
            dcg += rel / math.log2(idx + 2)

    # Ideal DCG
    ideal_rels = sorted(rel_scores, reverse=True)
    if not any(r > 0 for r in ideal_rels):
        # Fallback ideal if targets exist
        ideal_rels = [1.0] * min(k, len(target_docs))
    
    idcg = sum(r / math.log2(idx + 2) for idx, r in enumerate(ideal_rels[:k]))
    if idcg == 0:
        return 0.0
    return round(dcg / idcg, 4)


class SearchEvaluationService:
    """
    Evaluation module measuring Precision@K, Recall@K, MRR, NDCG@K, and Latency over benchmark search tasks.
    """
    def run_benchmark_eval(self, benchmark_tasks: List[BenchmarkQuery]) -> EvaluationMetricsResult:
        from app.services.query_pipeline import process_query_pipeline
        from app.services.hybrid_retrieval import hybrid_retrieval_service
        from app.services.reranker import ai_reranker_service

        if not benchmark_tasks:
            return EvaluationMetricsResult(
                total_queries=0,
                precision_at_1=0.0, precision_at_3=0.0, precision_at_5=0.0, precision_at_10=0.0,
                recall_at_1=0.0, recall_at_3=0.0, recall_at_5=0.0, recall_at_10=0.0,
                mrr=0.0, ndcg_at_5=0.0, ndcg_at_10=0.0, avg_latency_ms=0.0,
                query_details=[]
            )

        p1_list, p3_list, p5_list, p10_list = [], [], [], []
        r1_list, r3_list, r5_list, r10_list = [], [], [], []
        mrr_list = []
        ndcg5_list, ndcg10_list = [], []
        latencies = []
        query_details = []

        for task in benchmark_tasks:
            start_t = time.time()
            try:
                reformulation = process_query_pipeline(raw_query=task.query, mode="hybrid")
                candidates = hybrid_retrieval_service.retrieve_top_50(query=reformulation.best_query, top_k=50)
                reranked = ai_reranker_service.rerank_top_10(query=reformulation.best_query, candidate_chunks=candidates, top_k=10)
                elapsed_ms = round((time.time() - start_t) * 1000, 2)
                latencies.append(elapsed_ms)

                retrieved_filenames = [r["filename"] for r in reranked]

                p1 = calculate_precision_at_k(retrieved_filenames, task.target_filenames, 1)
                p3 = calculate_precision_at_k(retrieved_filenames, task.target_filenames, 3)
                p5 = calculate_precision_at_k(retrieved_filenames, task.target_filenames, 5)
                p10 = calculate_precision_at_k(retrieved_filenames, task.target_filenames, 10)

                r1 = calculate_recall_at_k(retrieved_filenames, task.target_filenames, 1)
                r3 = calculate_recall_at_k(retrieved_filenames, task.target_filenames, 3)
                r5 = calculate_recall_at_k(retrieved_filenames, task.target_filenames, 5)
                r10 = calculate_recall_at_k(retrieved_filenames, task.target_filenames, 10)

                rr = calculate_reciprocal_rank(retrieved_filenames, task.target_filenames)
                ndcg5 = calculate_ndcg_at_k(retrieved_filenames, task.target_filenames, 5)
                ndcg10 = calculate_ndcg_at_k(retrieved_filenames, task.target_filenames, 10)

                p1_list.append(p1)
                p3_list.append(p3)
                p5_list.append(p5)
                p10_list.append(p10)
                r1_list.append(r1)
                r3_list.append(r3)
                r5_list.append(r5)
                r10_list.append(r10)
                mrr_list.append(rr)
                ndcg5_list.append(ndcg5)
                ndcg10_list.append(ndcg10)

                query_details.append({
                    "query": task.query,
                    "best_query": reformulation.best_query,
                    "target_filenames": task.target_filenames,
                    "retrieved_filenames": retrieved_filenames,
                    "precision_at_5": p5,
                    "recall_at_5": r5,
                    "reciprocal_rank": rr,
                    "ndcg_at_5": ndcg5,
                    "latency_ms": elapsed_ms,
                })
            except Exception as e:
                logger.error(f"[EVALUATION] Error evaluating query '{task.query}': {str(e)}")

        count = max(1, len(latencies))
        return EvaluationMetricsResult(
            total_queries=len(benchmark_tasks),
            precision_at_1=round(sum(p1_list) / count, 4),
            precision_at_3=round(sum(p3_list) / count, 4),
            precision_at_5=round(sum(p5_list) / count, 4),
            precision_at_10=round(sum(p10_list) / count, 4),
            recall_at_1=round(sum(r1_list) / count, 4),
            recall_at_3=round(sum(r3_list) / count, 4),
            recall_at_5=round(sum(r5_list) / count, 4),
            recall_at_10=round(sum(r10_list) / count, 4),
            mrr=round(sum(mrr_list) / count, 4),
            ndcg_at_5=round(sum(ndcg5_list) / count, 4),
            ndcg_at_10=round(sum(ndcg10_list) / count, 4),
            avg_latency_ms=round(sum(latencies) / count, 2),
            query_details=query_details,
        )


evaluation_service = SearchEvaluationService()
