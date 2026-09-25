import logging
from typing import Optional
from app.core.config import settings

logger = logging.getLogger(__name__)

_chroma_client = None

def get_chroma_client():
    """
    Get or initialize ChromaDB Persistent Client.
    Handles imports and initialization errors gracefully.
    """
    global _chroma_client
    if _chroma_client is not None:
        return _chroma_client

    try:
        import chromadb
        from chromadb.config import Settings as ChromaSettings

        _chroma_client = chromadb.PersistentClient(
            path=settings.CHROMADB_PATH,
            settings=ChromaSettings(anonymized_telemetry=False)
        )
        logger.info(f"ChromaDB client initialized at {settings.CHROMADB_PATH}")
        return _chroma_client
    except Exception as e:
        logger.warning(f"Failed to initialize ChromaDB persistent client: {str(e)}")
        return None


def get_chroma_status() -> dict:
    """
    Check health and connectivity of ChromaDB client.
    """
    client = get_chroma_client()
    if client is None:
        return {
            "status": "unavailable",
            "message": "ChromaDB client is not initialized or module not installed"
        }
    try:
        # Simple ping/version check
        version = getattr(client, "get_version", lambda: "active")()
        return {
            "status": "healthy",
            "version": str(version),
            "storage_path": settings.CHROMADB_PATH
        }
    except Exception as e:
        return {
            "status": "degraded",
            "error": str(e)
        }
