import sys
import io
import json
from unittest.mock import patch, MagicMock
import httpx
from fastapi.testclient import TestClient

# Ensure UTF-8 output
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from app.main import app
from app.services.reformulation.base import (
    parse_and_validate_candidates,
    RateLimitError,
    AuthError,
    ProviderTimeoutError,
    MalformedResponseError,
    ProviderUnavailableError,
)
from app.services.reformulation.groq_provider import GroqReformulationProvider
from app.services.reformulation.cloudflare_provider import CloudflareReformulationProvider
from app.services.reformulation.ollama_provider import OllamaReformulationProvider
from app.services.reformulation.sambanova_provider import SambaNovaReformulationProvider
from app.services.reformulation.service import MultiLLMReformulationService
from app.services.query_pipeline import process_query_pipeline

client = TestClient(app)


# =============================================================================
# 1. Structured Output Validation & Parsing Tests
# =============================================================================

def test_output_validation_json_array():
    print("\n[TEST 1] Output Validation: JSON Array")
    raw = '["postgres vector indexing guide", "pgvector performance tuning", "optimizing postgres hnsw"]'
    candidates = parse_and_validate_candidates(raw, "postgres vector index")
    assert len(candidates) == 3
    assert candidates[0] == "postgres vector indexing guide"
    print("  -> PASSED: Valid JSON array parsed correctly.")


def test_output_validation_markdown_code_block():
    print("\n[TEST 2] Output Validation: Markdown Code Block")
    raw = """Here are the search queries:
```json
[
  "chromadb vector store architecture",
  "fastapi async chromadb retrieval",
  "hybrid rrf score tuning chromadb"
]
```
Hope this helps!"""
    candidates = parse_and_validate_candidates(raw, "chromadb vector store")
    assert len(candidates) == 3
    assert "chromadb vector store architecture" in candidates
    print("  -> PASSED: Markdown fences stripped and JSON extracted.")


def test_output_validation_json_object_wrapper():
    print("\n[TEST 3] Output Validation: JSON Object Wrapper")
    raw = json.dumps({
        "candidates": [
            "nextjs app router server actions",
            "nextjs 15 client component optimization",
            "react suspense streaming in nextjs"
        ]
    })
    candidates = parse_and_validate_candidates(raw, "nextjs app router")
    assert len(candidates) == 3
    assert candidates[0] == "nextjs app router server actions"
    print("  -> PASSED: JSON object with 'candidates' key extracted.")


def test_output_validation_line_by_line_fallback():
    print("\n[TEST 4] Output Validation: Numbered List / Line Fallback")
    raw = """
1. "postgresql connection pool latency"
2. "asyncpg tuning for high throughput"
3. "sqlalchemy async engine postgres configuration"
"""
    candidates = parse_and_validate_candidates(raw, "postgresql latency")
    assert len(candidates) == 3
    assert candidates[0] == "postgresql connection pool latency"
    print("  -> PASSED: Fallback line-by-line regex parsed successfully.")


def test_output_validation_insufficient_candidates():
    print("\n[TEST 5] Output Validation: Insufficient Candidates Rejection")
    raw = '["single query only"]'
    try:
        parse_and_validate_candidates(raw, "single query")
        assert False, "Should have raised MalformedResponseError"
    except MalformedResponseError:
        print("  -> PASSED: MalformedResponseError correctly raised for single item.")


def test_output_validation_duplicate_filtering():
    print("\n[TEST 6] Output Validation: Duplicate Removal")
    raw = '["duplicate query", "Duplicate Query", "DUPLICATE QUERY", "unique alternative query"]'
    candidates = parse_and_validate_candidates(raw, "test query")
    assert len(candidates) == 2
    assert candidates[0].lower() == "duplicate query"
    assert candidates[1] == "unique alternative query"
    print("  -> PASSED: Case-insensitive duplicates filtered out.")


# =============================================================================
# 2. Provider Adapter Unit Tests (with Mocked HTTP)
# =============================================================================

def test_groq_adapter_success():
    print("\n[TEST 7] Groq Adapter: Success Response")
    provider = GroqReformulationProvider(api_key="mock_groq_key")
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "choices": [{
            "message": {
                "content": '["groq candidate 1", "groq candidate 2", "groq candidate 3"]'
            }
        }]
    }

    with patch("httpx.Client.post", return_value=mock_resp):
        res = provider.reformulate("fastapi latency", "TROUBLESHOOTING", ["FastAPI"])
        assert len(res) == 3
        assert res[0] == "groq candidate 1"
        print("  -> PASSED: Groq adapter reformulates successfully.")


def test_groq_adapter_429_ratelimit():
    print("\n[TEST 8] Groq Adapter: HTTP 429 Rate Limit Handling")
    provider = GroqReformulationProvider(api_key="mock_groq_key")
    mock_resp = MagicMock()
    mock_resp.status_code = 429

    with patch("httpx.Client.post", return_value=mock_resp):
        try:
            provider.reformulate("test query", "TECHNICAL_SEARCH", [])
            assert False, "Should have raised RateLimitError"
        except RateLimitError:
            print("  -> PASSED: Groq HTTP 429 raises RateLimitError without loop.")


def test_groq_adapter_auth_failure():
    print("\n[TEST 9] Groq Adapter: HTTP 401 Auth Failure")
    provider = GroqReformulationProvider(api_key="invalid_key")
    mock_resp = MagicMock()
    mock_resp.status_code = 401

    with patch("httpx.Client.post", return_value=mock_resp):
        try:
            provider.reformulate("test query", "TECHNICAL_SEARCH", [])
            assert False, "Should have raised AuthError"
        except AuthError:
            print("  -> PASSED: Groq HTTP 401 raises AuthError.")


def test_groq_adapter_timeout():
    print("\n[TEST 10] Groq Adapter: Timeout Handling")
    provider = GroqReformulationProvider(api_key="mock_key", timeout=1.0)

    with patch("httpx.Client.post", side_effect=httpx.TimeoutException("Read timed out")):
        try:
            provider.reformulate("test query", "TECHNICAL_SEARCH", [])
            assert False, "Should have raised ProviderTimeoutError"
        except ProviderTimeoutError:
            print("  -> PASSED: Groq timeout raises ProviderTimeoutError.")


def test_cloudflare_adapter_success():
    print("\n[TEST 11] Cloudflare Adapter: Success Response")
    provider = CloudflareReformulationProvider(
        account_id="mock_acc", api_token="mock_tok", model="@cf/meta/llama-3.1-8b-instruct"
    )
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "success": True,
        "result": {
            "response": '["cf alternative 1", "cf alternative 2", "cf alternative 3"]'
        }
    }

    with patch("httpx.Client.post", return_value=mock_resp):
        res = provider.reformulate("vector search", "TECHNICAL_SEARCH", ["Vector"])
        assert len(res) == 3
        assert res[0] == "cf alternative 1"
        print("  -> PASSED: Cloudflare adapter reformulates successfully.")


def test_cloudflare_adapter_429():
    print("\n[TEST 12] Cloudflare Adapter: HTTP 429 Fast Failover")
    provider = CloudflareReformulationProvider(account_id="acc", api_token="tok")
    mock_resp = MagicMock()
    mock_resp.status_code = 429

    with patch("httpx.Client.post", return_value=mock_resp):
        try:
            provider.reformulate("test", "GENERAL_SEARCH", [])
            assert False, "Should raise RateLimitError"
        except RateLimitError:
            print("  -> PASSED: Cloudflare 429 triggers RateLimitError.")


def test_ollama_adapter_success():
    print("\n[TEST 13] Ollama Adapter: Local Success Response")
    provider = OllamaReformulationProvider(base_url="http://localhost:11434", model="qwen2.5:3b")
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "message": {
            "content": '["ollama candidate 1", "ollama candidate 2", "ollama candidate 3"]'
        }
    }

    with patch("httpx.Client.post", return_value=mock_resp):
        res = provider.reformulate("qwen local query", "TECHNICAL_SEARCH", [])
        assert len(res) == 3
        assert res[0] == "ollama candidate 1"
        print("  -> PASSED: Ollama adapter parses local response.")


def test_ollama_adapter_connection_error():
    print("\n[TEST 14] Ollama Adapter: Daemon Unreachable Connection Error")
    provider = OllamaReformulationProvider(base_url="http://localhost:11434")

    with patch("httpx.Client.post", side_effect=httpx.ConnectError("Connection refused")):
        try:
            provider.reformulate("test", "TECHNICAL_SEARCH", [])
            assert False, "Should raise ProviderUnavailableError"
        except ProviderUnavailableError:
            print("  -> PASSED: Ollama ConnectError gracefully handled.")


def test_sambanova_adapter_429_immediate_failover():
    print("\n[TEST 15] SambaNova Adapter: Immediate 429 Failover")
    provider = SambaNovaReformulationProvider(api_key="mock_samba")
    mock_resp = MagicMock()
    mock_resp.status_code = 429

    with patch("httpx.Client.post", return_value=mock_resp):
        try:
            provider.reformulate("test", "TECHNICAL_SEARCH", [])
            assert False, "Should raise RateLimitError"
        except RateLimitError:
            print("  -> PASSED: SambaNova 429 fast-fails immediately.")


# =============================================================================
# 3. Multi-Provider Fallback Orchestration Tests
# =============================================================================

def test_service_fallback_chain_rate_limit_to_local_ollama():
    print("\n[TEST 16] MultiLLM Service: Hosted 429 Rate Limit -> Fallback to Local Ollama")
    service = MultiLLMReformulationService()

    # Mock Groq to return 429, Cloudflare to return 429, Gemini to fail, Ollama to succeed
    service.providers["groq"].is_configured = MagicMock(return_value=True)
    service.providers["groq"].reformulate = MagicMock(side_effect=RateLimitError("429 rate limit"))

    service.providers["cloudflare"].is_configured = MagicMock(return_value=True)
    service.providers["cloudflare"].reformulate = MagicMock(side_effect=RateLimitError("429 quota"))

    service.providers["gemini"].is_configured = MagicMock(return_value=True)
    service.providers["gemini"].reformulate = MagicMock(side_effect=RateLimitError("ResourceExhausted"))

    service.providers["ollama"].is_configured = MagicMock(return_value=True)
    service.providers["ollama"].reformulate = MagicMock(return_value=[
        "ollama fallback query 1", "ollama fallback query 2", "ollama fallback query 3"
    ])

    candidates, provider_used = service.reformulate(
        query="optimize vector search latency",
        intent="TROUBLESHOOTING",
        entities=["Vector"],
    )

    assert candidates is not None
    assert len(candidates) == 3
    assert "Ollama" in provider_used
    print(f"  -> PASSED: Hosted 429 failed over cleanly to {provider_used}.")


def test_service_fallback_to_algorithmic():
    print("\n[TEST 17] MultiLLM Service: All Providers Unavailable -> Algorithmic Fallback")
    service = MultiLLMReformulationService()

    for p in service.providers.values():
        p.is_configured = MagicMock(return_value=True)
        p.reformulate = MagicMock(side_effect=ProviderUnavailableError("Offline"))

    candidates, provider_used = service.reformulate(
        query="test query all offline",
        intent="GENERAL_SEARCH",
        entities=[],
    )

    assert candidates is None
    assert provider_used == "Algorithmic Fallback"
    print("  -> PASSED: Full fallback chain yields Algorithmic Fallback safely.")


# =============================================================================
# 4. Pipeline & End-to-End Search Integration Tests
# =============================================================================

def test_query_pipeline_integration():
    print("\n[TEST 18] Query Pipeline Integration (process_query_pipeline)")
    explainability = process_query_pipeline(
        raw_query="how to fix postgresl slow vector search in fastpi",
        mode="hybrid"
    )
    assert explainability.original_query == "how to fix postgresl slow vector search in fastpi"
    assert "PostgreSQL" in explainability.cleaned_query
    assert "FastAPI" in explainability.cleaned_query
    assert explainability.intent == "TROUBLESHOOTING"
    assert len(explainability.candidate_queries) >= 3
    assert explainability.best_query != ""
    assert explainability.provider_used is not None
    print(f"  -> PASSED: Pipeline generated best query: '{explainability.best_query}' (Provider: {explainability.provider_used})")


def test_search_execute_integration_with_reformulation():
    print("\n[TEST 19] Enterprise Search Execution with Reformulation")

    # Ingest a sample doc
    content = b"""PostgreSQL & ChromaDB Query Reformulation Guide:
Configure BAAI/bge-small-en-v1.5 embeddings with ChromaDB persistent storage.
Use Reciprocal Rank Fusion (RRF) with BM25 keyword matching for optimal latency.
FastAPI asynchronous endpoints deliver sub-100ms response times for vector search.
"""
    up_res = client.post(
        "/api/v1/ingest/upload",
        files={"file": ("reformulation_integration_guide.txt", content, "text/plain")}
    )
    assert up_res.status_code in [200, 201]
    doc_id = up_res.json()["document"]["document_id"]

    # Execute search
    search_payload = {
        "query": "how to optimize chromdb vector store latency in fastpi",
        "mode": "hybrid",
        "filters": {"department": "all", "file_type": "all", "min_relevance": 0.0},
        "page": 1,
        "page_size": 5
    }
    search_res = client.post("/api/v1/search/execute", json=search_payload)
    assert search_res.status_code == 200
    data = search_res.json()
    assert data["success"] is True
    assert "query_reformulation" in data
    assert data["query_reformulation"]["provider_used"] is not None
    assert data["total_results"] > 0
    found_filenames = [r["filename"] for r in data["results"]]
    assert "reformulation_integration_guide.txt" in found_filenames, f"Expected document in results, got: {found_filenames}"
    target_match = next(r for r in data["results"] if r["filename"] == "reformulation_integration_guide.txt")
    assert target_match["relevance_percentage"] >= 40

    # Cleanup
    client.delete(f"/api/v1/ingest/documents/{doc_id}")
    print(f"  -> PASSED: Search returned match with {target_match['relevance_percentage']}% relevance. Provider: {data['query_reformulation']['provider_used']}.")


# =============================================================================
# Main Test Runner
# =============================================================================

def run_all_reformulation_tests():
    print("================================================================================")
    print("DYNAMIC MULTI-LLM QUERY REFORMULATION — VERIFICATION TEST SUITE")
    print("================================================================================")

    # 1. Output Validation
    test_output_validation_json_array()
    test_output_validation_markdown_code_block()
    test_output_validation_json_object_wrapper()
    test_output_validation_line_by_line_fallback()
    test_output_validation_insufficient_candidates()
    test_output_validation_duplicate_filtering()

    # 2. Provider Adapters
    test_groq_adapter_success()
    test_groq_adapter_429_ratelimit()
    test_groq_adapter_auth_failure()
    test_groq_adapter_timeout()
    test_cloudflare_adapter_success()
    test_cloudflare_adapter_429()
    test_ollama_adapter_success()
    test_ollama_adapter_connection_error()
    test_sambanova_adapter_429_immediate_failover()

    # 3. Fallback Orchestration
    test_service_fallback_chain_rate_limit_to_local_ollama()
    test_service_fallback_to_algorithmic()

    # 4. Pipeline Integration
    test_query_pipeline_integration()
    test_search_execute_integration_with_reformulation()

    print("\n================================================================================")
    print("ALL 19 MULTI-LLM REFORMULATION TESTS PASSED 100%!")
    print("================================================================================")


if __name__ == "__main__":
    run_all_reformulation_tests()
