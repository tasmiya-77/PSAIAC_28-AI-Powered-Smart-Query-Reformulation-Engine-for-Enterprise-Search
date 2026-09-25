from typing import Dict, Any
from pydantic import BaseModel, Field


class VectorStoreStatus(BaseModel):
    status: str = Field(..., example="healthy")
    version: str = Field(default="unknown")
    storage_path: str = Field(default="")


class HealthCheckResponse(BaseModel):
    status: str = Field(..., example="ok")
    app_name: str
    version: str
    environment: str
    vector_store: Dict[str, Any]
