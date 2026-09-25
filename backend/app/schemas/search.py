from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from app.schemas.query import QueryExplainability


class SearchFilterOptions(BaseModel):
    department: Optional[str] = Field(default="all", description="Department filter (Engineering, Legal, HR, Finance, All)")
    file_type: Optional[str] = Field(default="all", description="File type filter (pdf, docx, txt, md, All)")
    upload_date_range: Optional[str] = Field(default="all", description="Upload date filter (7d, 30d, 1y, all)")
    min_relevance: Optional[float] = Field(default=0.0, ge=0.0, le=1.0, description="Minimum relevance score threshold")
    sort_by: Optional[str] = Field(default="relevance", description="Sort order: relevance, date_desc, date_asc")


class SearchRequest(BaseModel):
    query: str = Field(..., min_length=2, max_length=1000, description="Search query string")
    mode: Optional[str] = Field(default="hybrid", description="Search mode: hybrid, semantic, vector, lexical")
    filters: Optional[SearchFilterOptions] = Field(default_factory=SearchFilterOptions)
    page: int = Field(default=1, ge=1, description="Page number for pagination")
    page_size: int = Field(default=10, ge=1, le=50, description="Number of results per page")


class CitationItem(BaseModel):
    citation_id: str
    filename: str
    document_id: str
    chunk_index: int


class AiAnswerResponse(BaseModel):
    answer: str
    has_answer: bool
    confidence_score: float
    citations: List[CitationItem]


class SearchResultItem(BaseModel):
    document_id: str
    chunk_id: str
    filename: str
    file_type: str
    file_size_bytes: int
    upload_date: str
    department: str
    content: str
    highlighted_snippet: str
    relevance_score: float
    relevance_percentage: int
    confidence: str
    matched_keywords: List[str]
    chunk_index: int
    total_chunks: int
    rank: Optional[int] = Field(default=1, description="Final search result ranking position (1..10)")
    title: Optional[str] = Field(default=None, description="Document title/filename")
    passage: Optional[str] = Field(default=None, description="Relevant text passage snippet")
    keyword_score: Optional[float] = Field(default=0.0, description="BM25 lexical keyword relevance score")
    semantic_score: Optional[float] = Field(default=0.0, description="ChromaDB vector semantic similarity score (0.0 - 1.0)")
    rerank_score: Optional[float] = Field(default=0.0, description="BGE Cross-Encoder reranking relevance score")
    retrieval_method: Optional[str] = Field(default="Hybrid (BM25 + ChromaDB Vector)", description="Retrieval method used to fetch candidate document")
    explanation: Optional[str] = Field(default=None, description="Concise rationale explaining why this result was selected and ranked")
    why_selected: Optional[str] = Field(default=None, description="Detailed explanation breakdown for UI disclosure")




class SearchResponse(BaseModel):
    success: bool
    processing_time_ms: float
    total_results: int
    page: int
    page_size: int
    total_pages: int
    from_cache: bool
    query_reformulation: QueryExplainability
    ai_answer: AiAnswerResponse
    results: List[SearchResultItem]
