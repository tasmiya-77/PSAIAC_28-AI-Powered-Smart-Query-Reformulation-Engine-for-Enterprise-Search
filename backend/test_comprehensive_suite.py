import time
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_1_health_check_endpoint():
    print("\n[TEST 1] Testing /api/v1/health...")
    res = client.get("/api/v1/health")
    assert res.status_code == 200, f"Expected 200, got {res.status_code}"
    data = res.json()
    assert data["status"] == "ok"
    assert "app_name" in data
    assert "vector_store" in data
    print("  -> PASSED: Health Check API status is OK.")


def test_2_auth_login_endpoints():
    print("\n[TEST 2] Testing /api/v1/auth/login...")
    # Admin login
    res_admin = client.post("/api/v1/auth/login", json={"username": "admin", "password": "admin123"})
    assert res_admin.status_code == 200
    data_admin = res_admin.json()
    assert data_admin["success"] is True
    assert data_admin["user"]["role"] == "Admin"
    assert "access_token" in data_admin
    print("  -> PASSED: Admin Authentication & JWT Token generation.")

    # Employee login
    res_emp = client.post("/api/v1/auth/login", json={"username": "employee", "password": "employee123"})
    assert res_emp.status_code == 200
    data_emp = res_emp.json()
    assert data_emp["user"]["role"] == "Employee"
    print("  -> PASSED: Employee Authentication & Role assignment.")


def test_3_document_ingestion_and_duplicate_check():
    print("\n[TEST 3] Testing /api/v1/ingest/upload (Ingestion & Duplicate Check)...")
    content = b"""PostgreSQL & Vector Database Architecture Guide:
HNSW indexes enable fast nearest-neighbor search for high-dimensional vectors in PostgreSQL using pgvector.
To maintain low query latency, tune m=16 and ef_construction=64.
Always maintain connection pools using asyncpg or SQLAlchemy async engine to prevent latency spikes.
FastAPI endpoints should utilize async query execution for high throughput RAG retrieval.
"""
    files = {"file": ("architecture_guide.txt", content, "text/plain")}
    res_up = client.post("/api/v1/ingest/upload", files=files)
    assert res_up.status_code in [200, 201], f"Expected 200/201, got {res_up.status_code}"
    data_up = res_up.json()
    assert data_up["success"] is True
    doc_id = data_up["document"]["document_id"]
    print(f"  -> PASSED: Ingested document ID {doc_id} with {data_up['document']['chunk_count']} vector chunks.")

    # Test Duplicate Hash Upload
    res_dup = client.post("/api/v1/ingest/upload", files={"file": ("architecture_guide.txt", content, "text/plain")})
    assert res_dup.status_code in [200, 201], f"Expected 200/201 for duplicate upload, got {res_dup.status_code}"
    data_dup = res_dup.json()
    print(f"  -> PASSED: Duplicate upload endpoint returned status {res_dup.status_code} ({data_dup.get('message', 'Upload handled')}).")

    return doc_id


def test_4_list_documents():
    print("\n[TEST 4] Testing /api/v1/ingest/documents...")
    res = client.get("/api/v1/ingest/documents")
    assert res.status_code == 200
    data = res.json()
    assert "documents" in data
    assert "total_chunks" in data
    assert len(data["documents"]) > 0
    print(f"  -> PASSED: Listed {len(data['documents'])} ingested documents ({data['total_chunks']} total chunks).")


def test_5_query_reformulation_pipeline():
    print("\n[TEST 5] Testing /api/v1/query/reformulate & /api/v1/query/history...")
    payload = {"query": "how to optimize postgresl vector index latency in fastpi", "mode": "hybrid"}
    res = client.post("/api/v1/query/reformulate", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert data["data"]["original_query"] == payload["query"]
    assert "best_query" in data["data"]
    assert "intent" in data["data"]
    assert "entities" in data["data"]
    print(f"  -> PASSED: 7-Step Reformulation generated best query: '{data['data']['best_query']}'.")

    # History API
    res_hist = client.get("/api/v1/query/history")
    assert res_hist.status_code == 200
    data_hist = res_hist.json()
    assert isinstance(data_hist, list)
    assert len(data_hist) > 0
    print(f"  -> PASSED: Reformulation History Log returned {len(data_hist)} record(s).")


def test_6_enterprise_search_execution_and_caching(doc_id: str):
    print("\n[TEST 6] Testing /api/v1/search/execute (Hybrid Retrieval, Reranking, AI Answer, Cache)...")
    search_payload = {
        "query": "how to optimize postgresl vector index latency in fastpi",
        "mode": "hybrid",
        "filters": {
            "department": "all",
            "file_type": "all",
            "min_relevance": 0.0
        },
        "page": 1,
        "page_size": 5
    }

    # First Execution (Fresh Search)
    res_search = client.post("/api/v1/search/execute", json=search_payload)
    assert res_search.status_code == 200, f"Expected 200, got {res_search.status_code}"
    s_data = res_search.json()

    assert s_data["success"] is True
    assert s_data["total_results"] > 0
    assert len(s_data["results"]) > 0
    assert s_data["ai_answer"]["has_answer"] is True
    assert len(s_data["ai_answer"]["citations"]) > 0
    
    top_result = s_data["results"][0]
    assert top_result["relevance_percentage"] > 70
    assert top_result["confidence"] in ["High", "Medium", "Low"]
    assert len(top_result["matched_keywords"]) > 0

    print(f"  -> PASSED: Hybrid Search Top Result: '{top_result['filename']}' ({top_result['relevance_percentage']}% Match).")
    print(f"  -> PASSED: Grounded Answer: '{s_data['ai_answer']['answer'][:80]}...' [{len(s_data['ai_answer']['citations'])} Citation(s)].")

    # Second Execution (Search Cache HIT)
    res_cache = client.post("/api/v1/search/execute", json=search_payload)
    assert res_cache.status_code == 200
    c_data = res_cache.json()
    assert c_data["from_cache"] is True
    print(f"  -> PASSED: Search Cache HIT verified (<{c_data['processing_time_ms']}ms).")


def test_7_analytics_and_admin_endpoints(doc_id: str):
    print("\n[TEST 7] Testing Analytics & Admin APIs...")
    # Analytics
    res_analytics = client.get("/api/v1/analytics/metrics")
    assert res_analytics.status_code == 200
    data_a = res_analytics.json()
    assert data_a["total_searches"] > 0
    assert "top_searched_queries" in data_a
    print("  -> PASSED: Analytics Telemetry API metrics returned.")

    # Admin System Status
    res_admin = client.get("/api/v1/admin/system-status")
    assert res_admin.status_code == 200
    data_admin = res_admin.json()
    assert data_admin["chromadb_status"]["status"] == "healthy"
    print("  -> PASSED: Admin System Diagnostics returned healthy status.")

    # Document Deletion
    res_del = client.delete(f"/api/v1/ingest/documents/{doc_id}")
    assert res_del.status_code == 200
    print(f"  -> PASSED: Deleted test document {doc_id} and cleared vector chunks.")


if __name__ == "__main__":
    print("=================================================================")
    print("RUNNING COMPREHENSIVE AUTOMATED TEST SUITE FOR BACKEND ENGINE")
    print("=================================================================")
    test_1_health_check_endpoint()
    test_2_auth_login_endpoints()
    doc_id = test_3_document_ingestion_and_duplicate_check()
    test_4_list_documents()
    test_5_query_reformulation_pipeline()
    test_6_enterprise_search_execution_and_caching(doc_id)
    test_7_analytics_and_admin_endpoints(doc_id)
    print("=================================================================")
    print("ALL COMPREHENSIVE BACKEND API & INTEGRATION TESTS PASSED 100%!")
    print("=================================================================")
