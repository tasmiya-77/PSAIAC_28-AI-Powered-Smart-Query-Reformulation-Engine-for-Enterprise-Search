import time
import math
from typing import List
from fastapi import APIRouter, HTTPException, status
from app.schemas.search import (
    SearchRequest,
    SearchResponse,
    SearchResultItem,
    AiAnswerResponse,
)
from app.services.query_pipeline import process_query_pipeline
from app.services.hybrid_retrieval import hybrid_retrieval_service
from app.services.reranker import ai_reranker_service
from app.services.answer_generator import ai_answer_generator_service
from app.services.search_cache import search_cache

router = APIRouter()


@router.post(
    "/search/execute",
    response_model=SearchResponse,
    tags=["Enterprise Search"],
)
async def execute_enterprise_search(request: SearchRequest):
    """
    Execute full Enterprise Search pipeline:
    Cache Check -> Reformulation & Explainability -> Hybrid BM25+Vector Top 50 -> AI Cross-Encoder Rerank Top 10 -> Grounded AI Answer Generation -> Pagination.
    """
    if not request.query or not request.query.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Search query cannot be empty.",
        )

    start_time = time.time()
    filter_dict = request.filters.model_dump() if request.filters else {}
    mode = request.mode or "hybrid"

    # 1. Cache Check
    cached_data = search_cache.get(request.query, filter_dict, mode)
    if cached_data:
        cached_data["from_cache"] = True
        cached_data["processing_time_ms"] = round((time.time() - start_time) * 1000, 2)
        return SearchResponse(**cached_data)

    try:
        # 2. Query Reformulation & Explainability
        reformulation = process_query_pipeline(
            raw_query=request.query, mode=mode
        )
        effective_query = reformulation.best_query

        # 3. Hybrid Retrieval (Top 50 candidates)
        candidates_top_50 = hybrid_retrieval_service.retrieve_top_50(
            query=effective_query,
            filters=filter_dict,
            top_k=50
        )

        # 4. AI Cross-Encoder Reranking (Top 10 most relevant)
        reranked_top_10 = ai_reranker_service.rerank_top_10(
            query=effective_query,
            candidate_chunks=candidates_top_50,
            top_k=10
        )

        # Apply minimum relevance score filter
        min_rel = request.filters.min_relevance if request.filters else 0.0
        if min_rel > 0.0:
            reranked_top_10 = [d for d in reranked_top_10 if d["relevance_score"] >= min_rel]

        # 5. AI Grounded Answer Generation from Top 5
        ai_answer_dict = ai_answer_generator_service.generate_answer(
            query=request.query, top_results=reranked_top_10
        )
        ai_answer = AiAnswerResponse(**ai_answer_dict)

        # 6. Pagination
        total_results = len(reranked_top_10)
        page_size = request.page_size
        page_num = request.page
        total_pages = max(1, math.ceil(total_results / page_size)) if total_results > 0 else 1

        start_idx = (page_num - 1) * page_size
        end_idx = start_idx + page_size
        paginated_results = reranked_top_10[start_idx:end_idx]

        result_items = [SearchResultItem(**item) for item in paginated_results]
        elapsed_ms = round((time.time() - start_time) * 1000, 2)

        response_data = {
            "success": True,
            "processing_time_ms": elapsed_ms,
            "total_results": total_results,
            "page": page_num,
            "page_size": page_size,
            "total_pages": total_pages,
            "from_cache": False,
            "query_reformulation": reformulation,
            "ai_answer": ai_answer,
            "results": result_items,
        }

        # 7. Store in LRU Cache & Log to Query Store
        search_cache.set(request.query, filter_dict, mode, response_data)

        from app.services.query_store import query_store_service
        query_store_service.log_query(
            raw_query=request.query,
            best_query=effective_query,
            intent=reformulation.intent,
            confidence_score=reformulation.confidence_score,
            processing_time_ms=elapsed_ms,
            total_results=total_results,
            endpoint="/api/v1/search/execute",
        )

        return SearchResponse(**response_data)


    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred during enterprise search execution: {str(e)}",
        )
