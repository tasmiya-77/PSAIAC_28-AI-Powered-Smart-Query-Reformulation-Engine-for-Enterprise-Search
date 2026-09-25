import { QueryExplainability } from "@/types/api";

export interface SearchFilterOptions {
  department: string;
  file_type: string;
  upload_date_range: string;
  min_relevance: number;
  sort_by: string;
}

export interface SearchRequest {
  query: string;
  mode?: string;
  filters?: SearchFilterOptions;
  page?: number;
  page_size?: number;
}

export interface CitationItem {
  citation_id: string;
  filename: string;
  document_id: string;
  chunk_index: number;
}

export interface AiAnswerResponse {
  answer: string;
  has_answer: boolean;
  confidence_score: number;
  citations: CitationItem[];
}

export interface SearchResultItem {
  document_id: string;
  chunk_id: string;
  filename: string;
  file_type: string;
  file_size_bytes: number;
  upload_date: string;
  department: string;
  content: string;
  highlighted_snippet: string;
  relevance_score: number;
  relevance_percentage: number;
  confidence: "High" | "Medium" | "Low";
  matched_keywords: string[];
  chunk_index: number;
  total_chunks: number;
  rank?: number;
  title?: string;
  passage?: string;
  keyword_score?: number;
  semantic_score?: number;
  rerank_score?: number;
  retrieval_method?: string;
  explanation?: string;
  why_selected?: string;
}


export interface SearchResponse {
  success: boolean;
  processing_time_ms: number;
  total_results: number;
  page: number;
  page_size: number;
  total_pages: number;
  from_cache: boolean;
  query_reformulation: QueryExplainability;
  ai_answer: AiAnswerResponse;
  results: SearchResultItem[];
}
