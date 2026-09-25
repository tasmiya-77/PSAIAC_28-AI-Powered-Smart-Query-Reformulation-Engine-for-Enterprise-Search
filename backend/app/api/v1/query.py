import time
import uuid
from typing import List
from datetime import datetime
from fastapi import APIRouter, HTTPException, status
from app.schemas.query import QueryRequest, QueryResponse, QueryHistoryItem
from app.services.query_pipeline import process_query_pipeline

from app.services.query_store import query_store_service

router = APIRouter()


@router.post(
    "/query/reformulate",
    response_model=QueryResponse,
    tags=["Query Processing"],
)
async def reformulate_query(request: QueryRequest):
    """
    Process and reformulate raw user search query with full AI explainability.
    Executes: Normalization -> Spell Correction -> Intent Detection -> Entity Extraction -> Gemini AI Reformulation -> Candidate Ranking -> Explainability Reasoning.
    """
    if not request.query or not request.query.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Query string cannot be empty.",
        )

    start_time = time.time()

    try:
        explainability = process_query_pipeline(
            raw_query=request.query, mode=request.mode or "hybrid"
        )

        elapsed_ms = round((time.time() - start_time) * 1000, 2)

        # Store in persistent query history
        query_store_service.log_query(
            raw_query=explainability.original_query,
            best_query=explainability.best_query,
            intent=explainability.intent,
            confidence_score=explainability.confidence_score,
            processing_time_ms=elapsed_ms,
            endpoint="/api/v1/query/reformulate",
        )

        return QueryResponse(
            success=True,
            processing_time_ms=elapsed_ms,
            data=explainability,
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred during query reformulation: {str(e)}",
        )


@router.get(
    "/query/history",
    response_model=List[QueryHistoryItem],
    tags=["Query Processing"],
)
async def get_query_history():
    """
    Get recent query reformulation history logs.
    """
    raw_history = query_store_service.get_recent_history(50)
    return [
        QueryHistoryItem(
            id=item["query_id"],
            original_query=item["query"],
            best_query=item["best_query"],
            intent=item["intent"],
            confidence_score=item["confidence_score"],
            timestamp=item["timestamp"],
        )
        for item in raw_history
    ]

