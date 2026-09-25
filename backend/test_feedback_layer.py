import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)



def test_feedback_layer_e2e():
    print("=================================================================")
    print("TESTING USER FEEDBACK LAYER & ANALYTICS METRICS UPDATE")
    print("=================================================================")

    # 1. Submit positive feedback
    print("\n[STEP 1] Submitting Positive Feedback (👍 Helpful)...")
    fb_pos = {
        "query": "how to optimize postgresql vector index latency in fastapi",
        "reformulated_query": "how to optimize postgresql vector similarity latency in fastapi",
        "document_id": "doc_postgres_123",
        "chunk_id": "doc_postgres_123_chunk_0",
        "filename": "postgres_guide.txt",
        "rating": "helpful",
        "feedback_text": "Extremely accurate guide on HNSW index parameters m=16, ef_construction=64!"
    }
    res_pos = client.post("/api/v1/analytics/feedback", json=fb_pos)
    assert res_pos.status_code == 200, f"Expected 200, got {res_pos.status_code}"
    data_pos = res_pos.json()
    assert data_pos["success"] is True
    print(f"  -> PASSED: Positive feedback submitted. Feedback ID: {data_pos['feedback_id']}")

    # 2. Submit negative feedback
    print("\n[STEP 2] Submitting Negative Feedback (👎 Not Helpful)...")
    fb_neg = {
        "query": "nextjs 15 app router suspense boundaries",
        "reformulated_query": "nextjs app router suspense boundaries configuration",
        "document_id": "doc_nextjs_999",
        "chunk_id": "doc_nextjs_999_chunk_0",
        "filename": "legacy_react_guide.txt",
        "rating": "not_helpful",
        "feedback_text": "Result describes React 17 legacy router, not Next.js 15."
    }
    res_neg = client.post("/api/v1/analytics/feedback", json=fb_neg)
    assert res_neg.status_code == 200, f"Expected 200, got {res_neg.status_code}"
    data_neg = res_neg.json()
    assert data_neg["success"] is True
    print(f"  -> PASSED: Negative feedback submitted. Feedback ID: {data_neg['feedback_id']}")

    # 3. Test Duplicate Feedback Submission
    print("\n[STEP 3] Testing Duplicate Feedback Submission Handling...")
    res_dup = client.post("/api/v1/analytics/feedback", json=fb_pos)
    assert res_dup.status_code == 200
    data_dup = res_dup.json()
    assert "already recorded" in data_dup["message"].lower() or data_dup["success"] is True
    print("  -> PASSED: Duplicate feedback handled safely without error.")

    # 4. Fetch Feedback Statistics API
    print("\n[STEP 4] Fetching Feedback Statistics (/api/v1/analytics/feedback-stats)...")
    res_stats = client.get("/api/v1/analytics/feedback-stats")
    assert res_stats.status_code == 200
    stats = res_stats.json()

    assert stats["total_feedback_count"] >= 2
    assert "helpful_rate_percentage" in stats
    assert "not_helpful_rate_percentage" in stats
    assert "most_useful_documents" in stats
    assert "highest_success_queries" in stats
    assert "lowest_success_queries" in stats

    print(f"  -> PASSED: Total Feedback Count : {stats['total_feedback_count']}")
    print(f"  -> PASSED: Helpful Rate        : {stats['helpful_rate_percentage']}%")
    print(f"  -> PASSED: Not-Helpful Rate    : {stats['not_helpful_rate_percentage']}%")
    if stats["most_useful_documents"]:
        print(f"  -> PASSED: Top Useful Document : '{stats['most_useful_documents'][0]['filename']}' ({stats['most_useful_documents'][0]['helpful_count']} positive votes)")
    if stats["recent_feedback_comments"]:
        print(f"  -> PASSED: Recent Feedback Log  : {len(stats['recent_feedback_comments'])} comment(s) retrieved.")

    print("\n=================================================================")
    print("ALL USER FEEDBACK LAYER & ANALYTICS TESTS PASSED 100%!")
    print("=================================================================")


if __name__ == "__main__":
    test_feedback_layer_e2e()
