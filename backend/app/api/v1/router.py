from fastapi import APIRouter
from app.api.v1.health import router as health_router
from app.api.v1.auth import router as auth_router
from app.api.v1.query import router as query_router
from app.api.v1.ingest import router as ingest_router
from app.api.v1.search import router as search_router
from app.api.v1.analytics import router as analytics_router
from app.api.v1.admin import router as admin_router

api_router = APIRouter()
api_router.include_router(health_router)
api_router.include_router(auth_router)
api_router.include_router(query_router)
api_router.include_router(ingest_router)
api_router.include_router(search_router)
api_router.include_router(analytics_router)
api_router.include_router(admin_router)
