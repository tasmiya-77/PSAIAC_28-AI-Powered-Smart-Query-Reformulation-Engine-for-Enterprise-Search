from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class FeedbackSubmissionRequest(BaseModel):
    query: str = Field(..., min_length=1, description="Raw search query string")
    reformulated_query: Optional[str] = Field(default=None, description="Reformulated query used for search")
    document_id: str = Field(..., min_length=1, description="ID of the document being rated")
    chunk_id: Optional[str] = Field(default=None, description="Chunk ID if applicable")
    filename: Optional[str] = Field(default=None, description="Filename of document")
    rating: str = Field(..., description="Rating type: 'helpful' or 'not_helpful'")
    feedback_text: Optional[str] = Field(default=None, max_length=1000, description="Optional feedback comment")


class FeedbackSubmissionResponse(BaseModel):
    success: bool
    message: str
    feedback_id: str


class UsefulDocumentItem(BaseModel):
    document_id: str
    filename: str
    helpful_count: int
    not_helpful_count: int
    satisfaction_rate: float


class QuerySuccessItem(BaseModel):
    query: str
    total_feedback: int
    helpful_count: int
    success_rate: float


class FeedbackStatsResponse(BaseModel):
    total_feedback_count: int
    helpful_count: int
    not_helpful_count: int
    helpful_rate_percentage: float
    not_helpful_rate_percentage: float
    most_useful_documents: List[UsefulDocumentItem]
    highest_success_queries: List[QuerySuccessItem]
    lowest_success_queries: List[QuerySuccessItem]
    recent_feedback_comments: List[Dict[str, Any]]
