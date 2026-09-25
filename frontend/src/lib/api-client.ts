import { HealthCheckResponse, ApiError, DocumentListItem } from "@/types/api";
import { SearchRequest, SearchResponse } from "@/types/search";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000/api/v1";

export class ApiClient {
  private baseUrl: string;

  constructor(baseUrl: string = API_BASE_URL) {
    this.baseUrl = baseUrl;
  }

  private async request<T>(
    endpoint: string,
    options?: RequestInit
  ): Promise<T> {
    const url = `${this.baseUrl}${endpoint.startsWith("/") ? endpoint : `/${endpoint}`}`;

    try {
      const response = await fetch(url, {
        headers: {
          "Content-Type": "application/json",
          ...options?.headers,
        },
        ...options,
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        const error: ApiError = {
          message:
            errorData.detail ||
            errorData.message ||
            `HTTP error! status: ${response.status}`,
          status: response.status,
          details: errorData,
        };
        throw error;
      }

      return (await response.json()) as T;
    } catch (error) {
      if ((error as ApiError).status !== undefined) {
        throw error;
      }
      const networkError: ApiError = {
        message:
          error instanceof Error
            ? error.message
            : "Failed to connect to backend server",
        status: 0,
      };
      throw networkError;
    }
  }

  /**
   * Health check endpoint
   */
  async getHealthStatus(): Promise<HealthCheckResponse> {
    return this.request<HealthCheckResponse>("/health");
  }

  /**
   * Execute Enterprise Hybrid Search
   */
  async executeSearch(payload: SearchRequest): Promise<SearchResponse> {
    return this.request<SearchResponse>("/search/execute", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  }

  /**
   * Fetch list of ingested vector documents
   */
  async getDocuments(): Promise<{ documents: DocumentListItem[]; total_chunks: number }> {
    return this.request<{ documents: DocumentListItem[]; total_chunks: number }>("/ingest/documents");
  }

  /**
   * Upload and ingest a document
   */
  async uploadDocument(file: File): Promise<any> {
    const formData = new FormData();
    formData.append("file", file);

    const url = `${this.baseUrl}/ingest/upload`;
    const response = await fetch(url, {
      method: "POST",
      body: formData,
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw {
        message: errorData.detail || "Upload failed",
        status: response.status,
      };
    }
    return response.json();
  }

  /**
   * Delete an ingested document by document_id
   */
  async deleteDocument(documentId: string): Promise<any> {
    return this.request<any>(`/ingest/documents/${documentId}`, {
      method: "DELETE",
    });
  }

  /**
   * Fetch real-time analytics telemetry metrics
   */
  async getAnalyticsMetrics(): Promise<any> {
    return this.request<any>("/analytics/metrics");
  }

  /**
   * Fetch admin system diagnostics & status
   */
  async getAdminSystemStatus(): Promise<any> {
    return this.request<any>("/admin/system-status");
  }

  /**
   * Re-index vector collection
   */
  async reindexCollection(): Promise<any> {
    return this.request<any>("/admin/reindex", {
      method: "POST",
    });
  }

  /**
   * Submit user relevance feedback (helpful / not_helpful)
   */
  async submitFeedback(payload: {
    query: string;
    reformulated_query?: string;
    document_id: string;
    chunk_id?: string;
    filename?: string;
    rating: "helpful" | "not_helpful";
    feedback_text?: string;
  }): Promise<any> {
    return this.request<any>("/analytics/feedback", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  }

  /**
   * Fetch feedback statistics
   */
  async getFeedbackStats(): Promise<any> {
    return this.request<any>("/analytics/feedback-stats");
  }
}

export const apiClient = new ApiClient();

