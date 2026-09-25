export interface VectorStoreStatus {
  status: "healthy" | "degraded" | "unavailable";
  version?: string;
  storage_path?: string;
  message?: string;
  error?: string;
}

export interface HealthCheckResponse {
  status: "ok" | "degraded" | "error";
  app_name: string;
  version: string;
  environment: string;
  vector_store: VectorStoreStatus;
}

export interface ApiError {
  message: string;
  status?: number;
  details?: unknown;
}

export interface CandidateQuery {
  query: string;
  rank: number;
  score: number;
  strategy: string;
}

export interface QueryExplainability {
  original_query: string;
  cleaned_query: string;
  best_query: string;
  candidate_queries: CandidateQuery[];
  intent: string;
  entities: string[];
  added_keywords: string[];
  confidence_score: number;
  explanation: string;
}

export interface DocumentListItem {
  document_id: string;
  filename: string;
  file_type: string;
  file_size_bytes: number;
  chunk_count: number;
  upload_date: string;
}
