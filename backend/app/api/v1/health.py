from fastapi import APIRouter
from app.core.config import settings
from app.core.db import get_chroma_status
from app.schemas.health import HealthCheckResponse

router = APIRouter()


@router.get("/health", response_model=HealthCheckResponse, tags=["Health"])
async def check_health():
    """
    Returns system health status including ChromaDB connection status.
    """
    chroma_info = get_chroma_status()
    return HealthCheckResponse(
        status="ok",
        app_name=settings.PROJECT_NAME,
        version=settings.VERSION,
        environment=settings.ENVIRONMENT,
        vector_store=chroma_info
    )
