from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Dict, Any
from app.services.vector_store import vector_store_service
from app.schemas.feedback import FeedbackSubmissionRequest, FeedbackSubmissionResponse, FeedbackStatsResponse

router = APIRouter()



class AnalyticsMetricsResponse(BaseModel):
    total_documents: int
    total_chunks: int
    total_searches: int
    successful_reformulations: int
    avg_response_time_ms: float
    top_searched_queries: List[Dict[str, Any]]
    most_accessed_documents: List[Dict[str, Any]]
    search_trends: List[Dict[str, Any]]
    user_activity_summary: Dict[str, Any]


@router.get(
    "/analytics/metrics",
    response_model=AnalyticsMetricsResponse,
    tags=["Analytics"],
)
async def get_analytics_metrics():
    """
    Get real-time system analytics and search performance telemetry.
    """
    from app.services.query_store import query_store_service
    from app.services.feedback_service import feedback_service

    docs, total_chunks = vector_store_service.list_documents()
    qs_analytics = query_store_service.get_analytics_metrics()
    fb_stats = feedback_service.get_feedback_stats()

    most_accessed = [
        {
            "filename": doc.filename,
            "file_type": doc.filename.split(".")[-1] if "." in doc.filename else "txt",
            "access_count": doc.helpful_count + doc.not_helpful_count + 1,
        }
        for doc in fb_stats.most_useful_documents[:5]
    ]

    if not most_accessed and docs:
        most_accessed = [
            {"filename": d["filename"], "file_type": d["file_type"], "access_count": 1}
            for d in docs[:5]
        ]

    return AnalyticsMetricsResponse(
        total_documents=len(docs),
        total_chunks=total_chunks,
        total_searches=qs_analytics["total_searches"],
        successful_reformulations=qs_analytics["successful_reformulations"],
        avg_response_time_ms=qs_analytics["avg_response_time_ms"],
        top_searched_queries=qs_analytics["top_searched_queries"],
        most_accessed_documents=most_accessed,
        search_trends=qs_analytics["search_trends"],
        user_activity_summary=qs_analytics["user_activity_summary"],
    )



@router.get(
    "/analytics/evaluation",
    tags=["Analytics"],
)
async def get_evaluation_metrics():
    """
    Run evaluation benchmark against ground truth test suite and return measured IR metrics.
    Computes Precision@K, Recall@K, MRR, NDCG@K, and Latency.
    """
    from app.services.evaluation import evaluation_service, BenchmarkQuery

    docs, _ = vector_store_service.list_documents()
    sample_files = [d["filename"] for d in docs] if docs else ["postgres_guide.txt", "chroma_guide.docx", "gemini_arch.pdf"]

    tasks = [
        BenchmarkQuery(
            query="how to optimize postgresql vector index latency in fastapi",
            target_filenames=[f for f in sample_files if "postgres" in f.lower()] or ["postgres_guide.txt"],
            description="PostgreSQL vector similarity latency optimization query"
        ),
        BenchmarkQuery(
            query="chromadb vector store performance tuning best practices",
            target_filenames=[f for f in sample_files if "chroma" in f.lower()] or ["chroma_guide.docx"],
            description="ChromaDB persistent client optimization query"
        ),
        BenchmarkQuery(
            query="gemini query reformulation architecture",
            target_filenames=[f for f in sample_files if "gemini" in f.lower()] or ["gemini_arch.pdf"],
            description="Gemini AI query reformulation query"
        ),
    ]

    res = evaluation_service.run_benchmark_eval(tasks)
    return res


@router.post(
    "/analytics/feedback",
    response_model=FeedbackSubmissionResponse,
    tags=["Analytics Feedback"],
)
async def submit_user_feedback(request: FeedbackSubmissionRequest):
    """
    Submit user relevance feedback (helpful / not_helpful) for a search result item.
    """
    from app.services.feedback_service import feedback_service
    from fastapi import HTTPException, status

    try:
        return feedback_service.submit_feedback(request)
    except ValueError as ve:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(ve),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to submit feedback: {str(e)}",
        )


@router.get(
    "/analytics/feedback-stats",
    response_model=FeedbackStatsResponse,
    tags=["Analytics Feedback"],
)
async def get_feedback_statistics():
    """
    Get aggregated user feedback telemetry metrics: Helpful Rate, Not-Helpful Rate, Query Success Rankings, Most Useful Documents.
    """
    from app.services.feedback_service import feedback_service
    from fastapi import HTTPException, status

    try:
        return feedback_service.get_feedback_stats()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch feedback statistics: {str(e)}",
        )


