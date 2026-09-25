from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class DocumentMetadata(BaseModel):
    document_id: str = Field(..., description="Unique document ID (SHA-256 hash or UUID)")
    filename: str = Field(..., description="Original filename")
    file_type: str = Field(..., description="File extension/type (pdf, docx, txt, md)")
    file_size_bytes: int = Field(..., description="File size in bytes")
    file_hash: str = Field(..., description="SHA-256 content hash")
    chunk_count: int = Field(..., description="Total semantic chunks generated")
    upload_date: str = Field(..., description="ISO timestamp of upload")
    extra_metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)


class DocumentUploadResponse(BaseModel):
    success: bool
    message: str
    document: DocumentMetadata


class DocumentListItem(BaseModel):
    document_id: str
    filename: str
    file_type: str
    file_size_bytes: int
    chunk_count: int
    upload_date: str


class DocumentListResponse(BaseModel):
    total_documents: int
    total_chunks: int
    documents: List[DocumentListItem]


class DocumentDeleteResponse(BaseModel):
    success: bool
    message: str
    document_id: str
    deleted_chunks: int
