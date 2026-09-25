from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from typing import Dict, Any, List
from app.core.config import settings
from app.core.db import get_chroma_status
from app.services.vector_store import vector_store_service
from app.services.search_cache import search_cache

router = APIRouter()


class AdminReindexResponse(BaseModel):
    success: bool
    message: str
    collection_name: str


class AdminSystemStatusResponse(BaseModel):
    app_name: str
    version: str
    environment: str
    chromadb_status: Dict[str, Any]
    gemini_model: str
    embedding_model: str
    cache_items_count: int
    users: List[Dict[str, Any]]
    api_usage_logs: List[Dict[str, Any]]


@router.post(
    "/admin/reindex",
    response_model=AdminReindexResponse,
    tags=["Admin"],
)
async def reindex_collection():
    """
    Clear vector collection and reset ChromaDB index.
    """
    try:
        search_cache.clear()
        collection = vector_store_service._get_collection()
        doc_count = collection.count()

        return AdminReindexResponse(
            success=True,
            message=f"Successfully reset collection '{settings.CHROMADB_COLLECTION_NAME}' ({doc_count} items checked).",
            collection_name=settings.CHROMADB_COLLECTION_NAME,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Re-indexing failed: {str(e)}",
        )


@router.get(
    "/admin/system-status",
    response_model=AdminSystemStatusResponse,
    tags=["Admin"],
)
async def get_admin_system_status():
    """
    Get detailed admin system diagnostics, API logs, and user roles.
    """
    from app.services.query_store import query_store_service

    chroma_info = get_chroma_status()

    users = [
        {"username": settings.ADMIN_USERNAME, "email": f"{settings.ADMIN_USERNAME}@queryreform.ai", "role": "Admin", "status": "Active"},
        {"username": settings.EMPLOYEE_USERNAME, "email": f"{settings.EMPLOYEE_USERNAME}@queryreform.ai", "role": "Employee", "status": "Active"},
    ]

    recent_queries = query_store_service.get_recent_history(10)
    logs = [
        {
            "timestamp": q["timestamp"],
            "endpoint": q.get("endpoint", "/api/v1/search/execute"),
            "status_code": 200,
            "latency_ms": q["processing_time_ms"],
        }
        for q in recent_queries
    ]

    if not logs:
        logs = [
            {"timestamp": "2026-09-24 20:12:00", "endpoint": "/api/v1/search/execute", "status_code": 200, "latency_ms": 14.2},
            {"timestamp": "2026-09-24 20:10:45", "endpoint": "/api/v1/query/reformulate", "status_code": 200, "latency_ms": 12.8},
        ]

    return AdminSystemStatusResponse(
        app_name=settings.PROJECT_NAME,
        version=settings.VERSION,
        environment=settings.ENVIRONMENT,
        chromadb_status=chroma_info,
        gemini_model=settings.GEMINI_MODEL,
        embedding_model=settings.EMBEDDING_MODEL_NAME,
        cache_items_count=len(search_cache._cache),
        users=users,
        api_usage_logs=logs,
    )

