from typing import List, Optional
from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    query: str = Field(..., min_length=2, max_length=1000, description="Raw user search query")
    mode: Optional[str] = Field(default="hybrid", description="Search mode: hybrid, semantic, vector, lexical")


class CandidateQuery(BaseModel):
    query: str
    rank: int
    score: float = Field(..., ge=0.0, le=1.0)
    strategy: str = Field(..., description="Reformulation strategy used (e.g. synonym_expansion, intent_alignment)")


class QueryExplainability(BaseModel):
    original_query: str
    cleaned_query: str
    best_query: str
    candidate_queries: List[CandidateQuery]
    intent: str = Field(..., description="Detected user intent (e.g. TECHNICAL_SEARCH, TROUBLESHOOTING)")
    entities: List[str] = Field(default_factory=list, description="Extracted technical entities/terms")
    added_keywords: List[str] = Field(default_factory=list, description="Keywords injected during expansion")
    confidence_score: float = Field(..., ge=0.0, le=1.0)
    explanation: str = Field(..., description="Detailed rationale for query reformulation decision")
    provider_used: Optional[str] = Field(default=None, description="LLM provider used for reformulation (e.g. Groq, Cloudflare, Ollama, Gemini, Algorithmic)")


class QueryResponse(BaseModel):
    success: bool
    processing_time_ms: float
    data: QueryExplainability


class QueryHistoryItem(BaseModel):
    id: str
    original_query: str
    best_query: str
    intent: str
    confidence_score: float
    timestamp: str
