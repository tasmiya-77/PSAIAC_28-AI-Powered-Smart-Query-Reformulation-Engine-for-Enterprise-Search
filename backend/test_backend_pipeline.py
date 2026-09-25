from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health_endpoint():
    print("Testing /api/v1/health...")
    response = client.get("/api/v1/health")
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    data = response.json()
    assert data["status"] == "ok"
    print("[PASS] Health check PASSED:", data["app_name"])


def test_enterprise_search_execution():
    print("\nTesting Enterprise Search (/api/v1/search/execute)...")

    # Ingest document first
    doc_content = b"""PostgreSQL Vector Database Optimization:
To optimize PostgreSQL vector similarity performance, configure HNSW index parameters (m=16, ef_construction=64).
Always maintain connection pools using asyncpg or SQLAlchemy async engine to prevent connection latency spikes.
FastAPI endpoints should utilize async query execution for high throughput RAG retrieval.
"""
    files = {"file": ("postgres_rag_guide.txt", doc_content, "text/plain")}
    res_up = client.post("/api/v1/ingest/upload", files=files)
    assert res_up.status_code == 201
    doc_id = res_up.json()["document"]["document_id"]
    print(f"[PASS] Sample Document Ingested: {doc_id}")

    # Run Enterprise Search
    search_payload = {
        "query": "how to optimize postgresl vector index latency in fastpi",
        "mode": "hybrid",
        "filters": {
            "department": "all",
            "file_type": "all",
            "min_relevance": 0.0
        },
        "page": 1,
        "page_size": 10
    }

    res_search = client.post("/api/v1/search/execute", json=search_payload)
    assert res_search.status_code == 200, f"Expected 200, got {res_search.status_code}"
    s_data = res_search.json()
    
    assert s_data["success"] is True
    print(f"[PASS] Total Results: {s_data['total_results']}")
    print(f"[PASS] AI Answer: {s_data['ai_answer']['answer']}")
    print(f"[PASS] Citations Count: {len(s_data['ai_answer']['citations'])}")
    print(f"[PASS] Top Result Title: {s_data['results'][0]['filename']}")
    print(f"[PASS] Top Result Relevance: {s_data['results'][0]['relevance_percentage']}% ({s_data['results'][0]['confidence']})")
    print(f"[PASS] Matched Keywords: {s_data['results'][0]['matched_keywords']}")

    # Test cache hit
    res_cache = client.post("/api/v1/search/execute", json=search_payload)
    assert res_cache.status_code == 200
    assert res_cache.json()["from_cache"] is True
    print("[PASS] Search Cache HIT verified!")

    # Clean up document
    client.delete(f"/api/v1/ingest/documents/{doc_id}")
    print("[PASS] Test Cleanup Complete.")


if __name__ == "__main__":
    print("==========================================")
    print("RUNNING ENTERPRISE SEARCH TEST SUITE")
    print("==========================================")
    test_health_endpoint()
    test_enterprise_search_execution()
    print("==========================================")
    print("ALL ENTERPRISE SEARCH TESTS PASSED!")
    print("==========================================")
